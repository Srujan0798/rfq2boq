"""PDF extractor with bbox support for LayoutLM."""

from dataclasses import dataclass, field


@dataclass
class TokenWithBBox:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_number: int


@dataclass
class PageContentWithBBox:
    page_number: int
    text: str = ""
    tokens_with_bbox: list[TokenWithBBox] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0


class PDFExtractorWithBBox:
    """PDF extractor that captures bounding boxes for LayoutLM."""

    def extract_with_bboxes(self, pdf_path: str) -> list[PageContentWithBBox]:
        """Extract text and bounding boxes from PDF.

        Returns token-level bounding boxes normalized to 0-1000 range
        (LayoutLM convention).
        """
        try:
            import pdfplumber
        except ImportError:
            return []

        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_content = PageContentWithBBox(page_number=page_num)

                if page.width and page.height:
                    page_content.width = page.width
                    page_content.height = page.height

                text = page.extract_text() or ""
                page_content.text = text

                chars = page.chars
                if chars:
                    tokens = self._aggregate_chars_to_tokens(chars, page_num, page.width, page.height)
                    page_content.tokens_with_bbox = tokens

                pages.append(page_content)

        return pages

    def _aggregate_chars_to_tokens(
        self, chars: list[dict], page_num: int, page_width: float, page_height: float
    ) -> list[TokenWithBBox]:
        """Aggregate character-level bboxes to token level."""
        if not chars:
            return []

        words: list[TokenWithBBox] = []
        current_word: list[dict] = []
        current_bbox: tuple[float, float, float, float] | None = None

        for char in chars:
            if char.get("text", "").strip():
                if not current_word:
                    current_word = [char]
                    current_bbox = (
                        float(char["x0"]),
                        float(char["top"]),
                        float(char["x1"]),
                        float(char["bottom"]),
                    )
                elif current_bbox is not None and char["x0"] <= current_bbox[2] + 2:
                    current_word.append(char)
                    current_bbox = (
                        min(current_bbox[0], float(char["x0"])),
                        min(current_bbox[1], float(char["top"])),
                        max(current_bbox[2], float(char["x1"])),
                        max(current_bbox[3], float(char["bottom"])),
                    )
                else:
                    if current_word and current_bbox is not None:
                        words.append(self._make_token(current_word, current_bbox, page_num, page_width, page_height))
                    current_word = [char]
                    current_bbox = (
                        float(char["x0"]),
                        float(char["top"]),
                        float(char["x1"]),
                        float(char["bottom"]),
                    )
            else:
                if current_word and current_bbox is not None:
                    words.append(self._make_token(current_word, current_bbox, page_num, page_width, page_height))
                    current_word = []
                    current_bbox = None

        if current_word and current_bbox is not None:
            words.append(self._make_token(current_word, current_bbox, page_num, page_width, page_height))

        return words

    def _make_token(
        self,
        chars: list[dict],
        bbox: tuple[float, float, float, float],
        page_num: int,
        page_width: float,
        page_height: float,
    ) -> TokenWithBBox:
        """Create TokenWithBBox from characters and normalize coordinates."""
        text = "".join(c["text"] for c in chars)
        x0, y0, x1, y1 = bbox

        norm = 1000.0
        if page_width > 0 and page_height > 0:
            nx0 = float(int((x0 / page_width) * norm))
            ny0 = float(int((y0 / page_height) * norm))
            nx1 = float(int((x1 / page_width) * norm))
            ny1 = float(int((y1 / page_height) * norm))
        else:
            nx0, ny0, nx1, ny1 = 0.0, 0.0, norm, norm

        return TokenWithBBox(
            text=text,
            x0=nx0,
            y0=ny0,
            x1=nx1,
            y1=ny1,
            page_number=page_num,
        )

    def detect_tables(self, pdf_path: str) -> bool:
        """Detect if PDF contains tables."""
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables and any(t for t in tables if len(t) > 1):
                        return True
        except Exception:
            pass
        return False

    def detect_multi_column(self, pdf_path: str) -> bool:
        """Detect if PDF has multi-column layout."""
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    words = page.extract_words()
                    if len(words) < 10:
                        continue
                    x_positions = [w["x0"] for w in words]
                    median_x = sorted(x_positions)[len(x_positions) // 2]
                    left_count = sum(1 for x in x_positions if x < median_x - 50)
                    right_count = sum(1 for x in x_positions if x > median_x + 50)
                    if left_count > 0 and right_count > 0:
                        return True
        except Exception:
            pass
        return False
