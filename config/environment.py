import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("URL")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))