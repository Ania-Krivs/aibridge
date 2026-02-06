import os
from dotenv import load_dotenv

load_dotenv()

#from .env file
DATABASE_URL = os.environ.get("DATABASE_URL")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USER")
DB_NAME = os.environ.get("DB_NAME")
DB_PASS = os.environ.get("DB_PASS")

ADMIN_KEY = os.environ.get('ADMIN_KEY')
OPENAI_KEY = os.environ.get("OPENAI_KEY")