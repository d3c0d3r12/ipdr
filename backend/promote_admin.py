#!/usr/bin/env python3
"""
Promote a user to the admin role (and mark them approved) in MongoDB.

Admins bypass the new-user approval gate and can approve/reject other users.

Usage:
    python promote_admin.py [username]

Defaults to username "admin" if none is given.
"""
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"

    mongo_url = os.getenv("MONGODB_URL", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
    db_name = os.getenv("MONGODB_DB_NAME", "ipdr_tracking")

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=30000)
    db = client[db_name]

    user = db["users"].find_one({"username": username})
    if not user:
        print(f"❌ No user found with username '{username}'.")
        return 1

    db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {
            "role": "admin",
            "is_approved": True,
            "is_active": True,
            "approved_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    print(f"✅ '{username}' is now an admin (approved). They can approve other users.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
