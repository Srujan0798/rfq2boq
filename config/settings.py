"""Project-wide settings loaded from environment variables or .env file.

Usage:
    from config.settings import settings
    print(settings.MODEL_DIR)
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    # RFQ2BOQ_MODEL_DIR: Directory containing the NER model files
    RFQ2BOQ_MODEL_DIR: Path = Path("models/ner-bert-bilstm-crf-v1")

    # RFQ2BOQ_ONTOLOGY_DIR: Directory containing ontology JSON files (materials.json, standards.json, etc.)
    RFQ2BOQ_ONTOLOGY_DIR: Path = Path("src/ontology")

    # RFQ2BOQ_DATA_DIR: Root data directory for jobs, results, etc.
    RFQ2BOQ_DATA_DIR: Path = Path("data")

    # RFQ2BOQ_ANNOTATIONS_DIR: Directory for annotation files
    RFQ2BOQ_ANNOTATIONS_DIR: Path = Path("data/annotations")

    # RFQ2BOQ_TEMPLATES_DIR: Directory for report templates
    RFQ2BOQ_TEMPLATES_DIR: Path = Path("templates")

    # RFQ2BOQ_SCHEMA_DIR: Directory for JSON schemas
    RFQ2BOQ_SCHEMA_DIR: Path = Path("schema")

    # OCR
    # RFQ2BOQ_TESSERACT_CMD: Path to tesseract executable
    RFQ2BOQ_TESSERACT_CMD: str = "tesseract"

    # Quality gates
    # RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD: Minimum OCR confidence (0.0-1.0)
    RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD: float = 0.80

    # RFQ2BOQ_ENTITY_CONFIDENCE_THRESHOLD: Minimum entity confidence (0.0-1.0)
    RFQ2BOQ_ENTITY_CONFIDENCE_THRESHOLD: float = 0.70

    # RFQ2BOQ_RELATION_CONFIDENCE_THRESHOLD: Minimum relation confidence (0.0-1.0)
    RFQ2BOQ_RELATION_CONFIDENCE_THRESHOLD: float = 0.60

    # Processing limits
    # RFQ2BOQ_MAX_FILE_SIZE_MB: Maximum uploaded file size in MB
    RFQ2BOQ_MAX_FILE_SIZE_MB: int = 50

    # RFQ2BOQ_MAX_PAGES: Maximum number of pages to process per document
    RFQ2BOQ_MAX_PAGES: int = 200

    # Background job settings
    # RFQ2BOQ_JOB_LARGE_FILE_SIZE_MB: File size threshold (MB) for background processing
    RFQ2BOQ_JOB_LARGE_FILE_SIZE_MB: int = 5

    # RFQ2BOQ_JOB_LARGE_PAGE_COUNT: Page count threshold for background processing
    RFQ2BOQ_JOB_LARGE_PAGE_COUNT: int = 10

    # RFQ2BOQ_JOB_CLEANUP_HOURS: Hours after which completed jobs are auto-deleted
    RFQ2BOQ_JOB_CLEANUP_HOURS: int = 24

    # API settings
    # RFQ2BOQ_API_HOST: Host to bind the API server to
    RFQ2BOQ_API_HOST: str = "0.0.0.0"

    # RFQ2BOQ_API_PORT: Port to bind the API server to
    RFQ2BOQ_API_PORT: int = 8000

    # RFQ2BOQ_API_KEY: API key for authentication (empty = no auth)
    RFQ2BOQ_API_KEY: str = ""

    # CORS settings
    # RFQ2BOQ_CORS_ORIGINS: Comma-separated list of allowed CORS origins ("*" for all)
    RFQ2BOQ_CORS_ORIGINS: str = ""

    # Logging
    # RFQ2BOQ_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    RFQ2BOQ_LOG_LEVEL: str = "INFO"

    # Rate limiting
    # RFQ2BOQ_RATE_LIMIT: Rate limit for /v1/extract endpoint (e.g., "10/minute")
    RFQ2BOQ_RATE_LIMIT: str = "10/minute"

    # NER training
    # RFQ2BOQ_NER_LEARNING_RATE: Learning rate for BERT NER
    RFQ2BOQ_NER_LEARNING_RATE: float = 2e-5

    # RFQ2BOQ_NER_BILSTM_LR: Learning rate for BiLSTM layer
    RFQ2BOQ_NER_BILSTM_LR: float = 1e-3

    # RFQ2BOQ_NER_BATCH_SIZE: Training batch size
    RFQ2BOQ_NER_BATCH_SIZE: int = 16

    # RFQ2BOQ_NER_EPOCHS: Number of training epochs
    RFQ2BOQ_NER_EPOCHS: int = 8

    # RFQ2BOQ_NER_WARMUP_RATIO: Ratio of warmup steps
    RFQ2BOQ_NER_WARMUP_RATIO: float = 0.10

    # Relation extraction
    # RFQ2BOQ_RE_MAX_DISTANCE_CHARS: Maximum character distance for relation extraction
    RFQ2BOQ_RE_MAX_DISTANCE_CHARS: int = 500

    # RFQ2BOQ_RE_MAX_SENTENCE_GAP: Maximum sentence gap for relation extraction
    RFQ2BOQ_RE_MAX_SENTENCE_GAP: int = 3

    # Export
    # RFQ2BOQ_EXCEL_TEMPLATE: Path to Excel template file
    RFQ2BOQ_EXCEL_TEMPLATE: str = "templates/boq_template.xlsx"

    # Section filtering
    # RFQ2BOQ_SECTION_FILTER_ENABLED: Enable BOQ section detection to filter front matter
    RFQ2BOQ_SECTION_FILTER_ENABLED: bool = True

    @field_validator("RFQ2BOQ_LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if v.upper() not in valid_levels:
            return "INFO"
        return v.upper()

    @property
    def MODEL_DIR(self) -> Path:
        return self.RFQ2BOQ_MODEL_DIR

    @property
    def ONTOLOGY_DIR(self) -> Path:
        return self.RFQ2BOQ_ONTOLOGY_DIR

    @property
    def DATA_DIR(self) -> Path:
        return self.RFQ2BOQ_DATA_DIR

    @property
    def ANNOTATIONS_DIR(self) -> Path:
        return self.RFQ2BOQ_ANNOTATIONS_DIR

    @property
    def TEMPLATES_DIR(self) -> Path:
        return self.RFQ2BOQ_TEMPLATES_DIR

    @property
    def SCHEMA_DIR(self) -> Path:
        return self.RFQ2BOQ_SCHEMA_DIR

    @property
    def TESSERACT_CMD(self) -> str:
        return self.RFQ2BOQ_TESSERACT_CMD

    @property
    def OCR_CONFIDENCE_THRESHOLD(self) -> float:
        return self.RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD

    @property
    def ENTITY_CONFIDENCE_THRESHOLD(self) -> float:
        return self.RFQ2BOQ_ENTITY_CONFIDENCE_THRESHOLD

    @property
    def RELATION_CONFIDENCE_THRESHOLD(self) -> float:
        return self.RFQ2BOQ_RELATION_CONFIDENCE_THRESHOLD

    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        return self.RFQ2BOQ_MAX_FILE_SIZE_MB

    @property
    def MAX_PAGES(self) -> int:
        return self.RFQ2BOQ_MAX_PAGES

    @property
    def API_HOST(self) -> str:
        return self.RFQ2BOQ_API_HOST

    @property
    def API_PORT(self) -> int:
        return self.RFQ2BOQ_API_PORT

    @property
    def API_KEY(self) -> str:
        return self.RFQ2BOQ_API_KEY

    @property
    def CORS_ORIGINS(self) -> str:
        return self.RFQ2BOQ_CORS_ORIGINS

    @property
    def LOG_LEVEL(self) -> str:
        return self.RFQ2BOQ_LOG_LEVEL

    @property
    def RATE_LIMIT(self) -> str:
        return self.RFQ2BOQ_RATE_LIMIT

    @property
    def JOB_LARGE_FILE_SIZE_MB(self) -> int:
        return self.RFQ2BOQ_JOB_LARGE_FILE_SIZE_MB

    @property
    def JOB_LARGE_PAGE_COUNT(self) -> int:
        return self.RFQ2BOQ_JOB_LARGE_PAGE_COUNT

    @property
    def JOB_CLEANUP_HOURS(self) -> int:
        return self.RFQ2BOQ_JOB_CLEANUP_HOURS

    @property
    def NER_LEARNING_RATE(self) -> float:
        return self.RFQ2BOQ_NER_LEARNING_RATE

    @property
    def NER_BILSTM_LR(self) -> float:
        return self.RFQ2BOQ_NER_BILSTM_LR

    @property
    def NER_BATCH_SIZE(self) -> int:
        return self.RFQ2BOQ_NER_BATCH_SIZE

    @property
    def NER_EPOCHS(self) -> int:
        return self.RFQ2BOQ_NER_EPOCHS

    @property
    def NER_WARMUP_RATIO(self) -> float:
        return self.RFQ2BOQ_NER_WARMUP_RATIO

    @property
    def RE_MAX_DISTANCE_CHARS(self) -> int:
        return self.RFQ2BOQ_RE_MAX_DISTANCE_CHARS

    @property
    def RE_MAX_SENTENCE_GAP(self) -> int:
        return self.RFQ2BOQ_RE_MAX_SENTENCE_GAP

    @property
    def EXCEL_TEMPLATE(self) -> str:
        return self.RFQ2BOQ_EXCEL_TEMPLATE

    @property
    def SECTION_FILTER_ENABLED(self) -> bool:
        return self.RFQ2BOQ_SECTION_FILTER_ENABLED

    model_config = {"env_file": ".env", "env_prefix": "RFQ2BOQ_"}


settings = Settings()
