import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"

    # In-memory history limits
    MAX_HISTORY_RECORDS: int = 1000

    # Batch processing
    MAX_BULK_REVIEWS: int = 100
    MAX_CSV_ROWS: int = 500


settings = Settings()
