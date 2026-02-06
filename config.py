import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Yandex
    YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")
    YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
    YANDEX_LOGIN = os.getenv("YANDEX_LOGIN")
    YANDEX_PASSWORD = os.getenv("YANDEX_PASSWORD")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Google
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_secret.json")
    GOOGLE_FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID")
    GOOGLE_MASTER_SHEET_ID = os.getenv("GOOGLE_MASTER_SHEET_ID")
    
    @classmethod
    def check_deps(cls):
        missing = []
        if not cls.BOT_TOKEN: missing.append("BOT_TOKEN")
        if not cls.YANDEX_TOKEN: missing.append("YANDEX_TOKEN")
        if not cls.OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

config = Config()
