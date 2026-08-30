"""One-time, non-destructive MongoDB to SQLite data importer.

Run from the backend directory after keeping MONGODB_URL and DATABASE_NAME in
the environment or .env file. Existing SQLite rows with the same IDs are
updated; MongoDB is never modified.
"""
from pymongo import MongoClient

from app.config import settings
from app.my_database import (
    disaster_donation_request_collection,
    division_collection,
    donation_history_collection,
    donation_items_collection,
    relief_camp_collection,
    user_collection,
)

COLLECTIONS = {
    "users": user_collection,
    "disaster_donation_requests": disaster_donation_request_collection,
    "donation_history": donation_history_collection,
    "donation_items": donation_items_collection,
    "administrative_divisions": division_collection,
    "relief_camps": relief_camp_collection,
}


def main() -> None:
    client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=10_000)
    source = client[settings.DATABASE_NAME]
    try:
        for name, target in COLLECTIONS.items():
            count = 0
            for document in source[name].find({}):
                target.import_document(document)
                count += 1
            print(f"{name}: {count} document(s) copied")
    finally:
        client.close()


if __name__ == "__main__":
    main()
