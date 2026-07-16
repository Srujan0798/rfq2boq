"""OCR processor using Tesseract via pytesseract with image preprocessing."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass
class OCRWord:
    text: str
    conf: float
    bbox: tuple[int, int, int, int]


@dataclass
class OCRLine:
    words: list[OCRWord]
    text: str


@dataclass
class OCRPage:
    page_number: int
    text: str
    lines: list[OCRLine]
    conf_avg: float


@dataclass
class OCRResult:
    pages: list[OCRPage]
    conf_avg: float


class OCRProcessor:
    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.tesseract_cmd = tesseract_cmd

    @staticmethod
    def _preprocess_image(image):
        """Preprocess image for better OCR accuracy.

        Steps:
        1. Convert to grayscale
        2. Resize if too small (Tesseract works best at 300 DPI)
        3. Apply adaptive thresholding for binarization
        4. Denoise
        """
        from PIL import Image, ImageFilter, ImageOps

        # Convert to grayscale
        img = ImageOps.grayscale(image)

        # Resize if image is very small (minimum 1000px width for good OCR)
        min_width = 1000
        if img.width < min_width:
            ratio = min_width / img.width
            new_size = (min_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Apply mild sharpening
        img = img.filter(ImageFilter.SHARPEN)

        # Apply adaptive thresholding using point transform
        # This converts grayscale to black/white based on median brightness
        median = img.quantile(0.5)
        if median:
            threshold = int(median)
        else:
            # Fallback: compute histogram-based threshold
            hist = img.histogram()
            total = sum(hist)
            cumsum = 0
            threshold = 128
            for i, count in enumerate(hist):
                cumsum += count
                if cumsum >= total / 2:
                    threshold = i
                    break

        img = img.point(lambda x: 0 if x < threshold else 255, "1")
        img = img.convert("L")

        return img

    def process_image(self, image_path: str, lang: str = "eng") -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            img = self._preprocess_image(img)

            # Use Tesseract config optimized for document text
            # --psm 6: Assume a single uniform block of text
            # --oem 3: Use default engine mode
            custom_config = r"--oem 3 --psm 6"

            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config, lang=lang)
            pages = []
            conf_avg = 0.0
            if data.get("text"):
                lines_dict: dict[int, list[OCRWord]] = {}
                for i, text in enumerate(data["text"]):
                    conf = float(data["conf"][i]) / 100 if data["conf"][i] != "-1" else 0.0
                    if text.strip():
                        line_num = data["line_num"][i]
                        if line_num not in lines_dict:
                            lines_dict[line_num] = []
                        lines_dict[line_num].append(
                            OCRWord(
                                text=text,
                                conf=conf,
                                bbox=(
                                    data["left"][i],
                                    data["top"][i],
                                    data["width"][i],
                                    data["height"][i],
                                ),
                            )
                        )
                lines = []
                for line_num in sorted(lines_dict.keys()):
                    words = lines_dict[line_num]
                    line_text = " ".join(w.text for w in words)
                    lines.append(OCRLine(words=words, text=line_text))
                all_words = [word for line in lines for word in line.words]
                page_text = "\n".join(line.text for line in lines)
                page_conf = sum(word.conf for word in all_words) / len(all_words) if all_words else 0.0
                page = OCRPage(page_number=1, text=page_text, lines=lines, conf_avg=page_conf)
                pages.append(page)
                conf_avg = page.conf_avg
            return OCRResult(pages=pages, conf_avg=conf_avg)
        except Exception:
            return OCRResult(pages=[], conf_avg=0.0)

    def process_pdf(self, pdf_path: str, dpi: int = 300, max_pages: int | None = None) -> OCRResult:
        try:
            from pdf2image import convert_from_path

            if max_pages is not None:
                images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=max_pages)
            else:
                images = convert_from_path(pdf_path, dpi=dpi, first_page=1)
            all_pages = []
            conf_sum = 0.0
            with TemporaryDirectory() as tmpdir:
                for i, image in enumerate(images, start=1):
                    img_path = Path(tmpdir) / f"page_{i}.png"
                    image.save(img_path)
                    result = self.process_image(str(img_path))
                    for page in result.pages:
                        page.page_number = i
                        all_pages.append(page)
                    conf_sum += result.conf_avg
            return OCRResult(
                pages=all_pages,
                conf_avg=conf_sum / len(all_pages) if all_pages else 0.0,
            )
        except Exception:
            return OCRResult(pages=[], conf_avg=0.0)
