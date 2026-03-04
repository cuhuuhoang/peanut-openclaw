import os
import pymongo
from peanut_bridge.env import load_env

load_env()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "botdb")
MONGO_AUTH_DB = os.getenv("MONGO_AUTH_DB", "admin")


def get_db():
    if MONGO_USER and MONGO_PASS:
        uri = (
            f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
            f"{MONGO_DB}?authSource={MONGO_AUTH_DB}"
        )
        try:
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            return client[MONGO_DB]
        except Exception:
            pass

    # Fallback for local non-auth mongo
    uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
    client = pymongo.MongoClient(uri)
    return client[MONGO_DB]
