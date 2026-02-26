import json
import os
from pathlib import Path

from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Data directory
SEED_DIR = Path(__file__).resolve().parent.parent / "data" # ../data/

def main():
    mongo_uri = os.getenv("MONGO_URI")
    mongo_dbname = os.getenv("MONGO_DBNAME", "let_them_cook")
    if not mongo_uri:
        raise SystemExit("MONGO_URI must be set in .env")

    users_path = SEED_DIR / "users.json"
    recipes_path = SEED_DIR / "sample_recipes.json"
    if not users_path.exists():
        raise SystemExit(f"Seed users file not found: {users_path}")
    if not recipes_path.exists():
        raise SystemExit(f"Seed recipes file not found: {recipes_path}")

    with open(users_path, encoding="utf-8") as f:
        users_raw = json.load(f)
    with open(recipes_path, encoding="utf-8") as f:
        recipes_raw = json.load(f)

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=5000,
    )
    client.server_info()
    db = client[mongo_dbname]

    # Convert user _id and saved_recipes to ObjectIds; insert users first
    users = []
    for u in users_raw:
        user = dict(u)
        user["_id"] = ObjectId(user["_id"])
        user["saved_recipes"] = [ObjectId(rid) for rid in user.get("saved_recipes", [])]
        users.append(user)

    db.users.insert_many(users)
    print(f"Imported {len(users)} user(s) into {mongo_dbname}.users.")

    # Convert recipe author_id from JSON to ObjectId and insert
    recipes = []
    for r in recipes_raw:
        recipe = dict(r)
        if "author_id" in recipe:
            recipe["author_id"] = ObjectId(recipe["author_id"])
        recipes.append(recipe)

    result = db.recipes.insert_many(recipes)
    print(f"Imported {len(result.inserted_ids)} recipe(s) into {mongo_dbname}.recipes.")

if __name__ == "__main__":
    main()
