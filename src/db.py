import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]


def get_database_engine():
    return create_engine(DATABASE_URL)
