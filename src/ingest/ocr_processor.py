"""OCR processor using Tesseract via pytesseract."""

from dataclasses import dataclass


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

    def process_image(self, image_path: str, lang: str = "eng") -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
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
                        lines_dict[line_num].append(OCRWord(
                            text=text,
                            conf=conf,
                            bbox=(
                                data["left"][i],
                                data["top"][i],
                                data["width"][i],
                                data["height"][i],
                            ),
                        ))
                lines = []
                for line_num in sorted(lines_dict.keys()):
                    words = lines_dict[line_num]
                    line_text = " ".join(w.text for w in words)
                    lines.append(OCRLine(words=words, text=line_text))
                all_words = [word for line in lines for word in line.words]
                page_text = " ".join(line.text for line in lines)
                page_conf = sum(word.conf for word in all_words) / len(all_words) if all_words else 0.0
                page = OCRPage(page_number=1, text=page_text, lines=lines, conf_avg=page_conf)
                pages.append(page)
                conf_avg = page.conf_avg
            return OCRResult(pages=pages, conf_avg=conf_avg)
        except Exception:
            return OCRResult(pages=[], conf_avg=0.0)

    def process_pdf(self, pdf_path: str, dpi: int = 300) -> OCRResult:
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(pdf_path, dpi=dpi)
            all_pages = []
            conf_sum = 0.0
            for i, image in enumerate(images, start=1):
                img_path = f"/tmp/page_{i}.png"
                image.save(img_path)
                result = self.process_image(img_path)
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
