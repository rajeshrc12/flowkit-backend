from pymongo import MongoClient
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    _client: MongoClient = None
    _db = None

    @classmethod
    def connect(cls):
        if cls._client is None:
            mongo_url = os.getenv("DATABASE_URL")
            if not mongo_url:
                raise Exception("DATABASE_URL not found in .env")

            cls._client = MongoClient(mongo_url)

            # Extract DB name from URL
            parsed = urlparse(mongo_url)
            db_name = parsed.path.lstrip("/")  # removes leading slash
            if not db_name:
                raise Exception("Database name must be part of the DATABASE_URL")
            cls._db = cls._client[db_name]

    @classmethod
    def get_collection(cls, name: str):
        if cls._db is None:
            cls.connect()
        return cls._db[name]
