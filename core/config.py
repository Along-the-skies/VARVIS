# Jarvis Configuration

import os
from dotenv import load_dotenv


load_dotenv()


JARVIS_NAME = "Jarvis"

DEBUG = True

API_KEY = os.getenv("API_KEY")