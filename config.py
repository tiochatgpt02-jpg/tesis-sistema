import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env', override=False)


class Config:
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'groq').strip().lower()
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
    NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
    NVIDIA_MODEL = os.getenv('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')
    AI_TIMEOUT_SECONDS = max(1, min(60, int(os.getenv('AI_TIMEOUT_SECONDS', '25'))))
    AI_MAX_OUTPUT_TOKENS = max(256, min(8192, int(os.getenv('AI_MAX_OUTPUT_TOKENS', '3000'))))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() in {'1', 'true', 'yes', 'on'}
    ML_DATASET_SOURCE = os.getenv('ML_DATASET_SOURCE', 'benchmark').strip().lower()

    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'sistema_ia')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')

    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
