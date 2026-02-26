import os
from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "dev" # change this to an environment variable later

# ---------------------------------------------------------------------------
# MongoDB connection. Set MONGO_URI in .env.
# ---------------------------------------------------------------------------
mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME", "let_them_cook")
if not mongo_uri:
    raise RuntimeError("MONGO_URI must be set in .env to connect to MongoDB.")
client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
    socketTimeoutMS=5000,
)
client.server_info() # force connection check
db = client[mongo_dbname]
print(" * Connected to MongoDB successfully.")
recipes_collection = db.recipes

# ---------------------------------------------------------------------------
# Flask login setup
# ---------------------------------------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # redirect here if not logged in

class User(UserMixin):
    def __init__(self, user):
        self.id = user["_id"]
        self.email = user["email"]
        self.username = user["username"]

@login_manager.user_loader
def load_user(user_id):
    # session stores user's _id; load user by _id
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = db.users.find_one({"_id": oid})
        if user:
            return User(user)
    except Exception:
        pass
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        # check the database
        user = db.users.find_one({"email": email})
        if user and user["password"] == password:
            login_user(User(user))
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not email or not username or not password:
            return render_template("signup.html", error="All fields are required.")

        if db.users.find_one({"email": email}):
            return render_template("signup.html", error="Email already taken.")

        db.users.insert_one({
            "email": email,
            "username": username,
            "password": password,
            "saved_recipes": []
        })

        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------

@app.route("/")
@login_required
def home():
    """Display all recipes on the home page."""
    recipes = list(recipes_collection.find())
    return render_template("home.html", recipes=recipes)


@app.route("/menu")
@login_required
def menu():
    """Display navigation menu page."""
    return render_template("menu.html")


@app.route("/create-recipe", methods=["GET", "POST"])
@login_required
def create_recipe():
    """Create a new recipe."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "")
        ingredients_raw = request.form.get("ingredients", "")
        prep_time = request.form.get("prep_time", "")
        instructions_raw = request.form.get("instructions", "")

        # Parse ingredients (comma separated)
        ingredients = [i.strip() for i in ingredients_raw.split(",") if i.strip()]
        # Parse instructions (newline separated)
        instructions = [i.strip() for i in instructions_raw.split("\n") if i.strip()]

        if name:
            recipes_collection.insert_one(
                {
                    "name": name,
                    "description": description,
                    "ingredients": ingredients,
                    "prep_time": int(prep_time) if prep_time else None,
                    "instructions": instructions,
                    "author_id": current_user.id
                }
            )
        return redirect(url_for("home"))

    return render_template("create_recipe.html")


@app.route("/profile")
@login_required
def profile():
    user = db.users.find_one({"_id": ObjectId(current_user.id)})

    saved_ids = user.get("saved_recipes", [])
    saved_recipes = list(
        recipes_collection.find({"_id": {"$in": saved_ids}})
    )

    user_recipes = list(
        recipes_collection.find({"author_id": current_user.id})
    )

    return render_template("profile.html", saved_recipes=saved_recipes, user_recipes=user_recipes)

@app.route("/profile/<user_id>")
@login_required
def view_user_profile(user_id):
    """ Display another user's profile"""
    user = db.users.find_one({"_id": ObjectId(user_id)})
    saved_ids = user.get("saved_recipes", [])
    saved_recipes = list(
        recipes_collection.find({"_id": {"$in": saved_ids}})
    )
    user_recipes = list(
        recipes_collection.find({"author_id": user["_id"]})
    )
    return render_template("user_profile.html", user=user, saved_recipes=saved_recipes, user_recipes=user_recipes)


@app.route("/recipe/<recipe_id>")
@login_required
def view_recipe(recipe_id):
    """View a single recipe's details."""
    ## Get the recipe object from database
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})

    ## Get the original poster's object from database
    ## work backwards from recipe
    ## recipe is a dictionary so must use [""]
    user = db.users.find_one({"_id": recipe["author_id"]})
    return render_template("recipe.html", recipe=recipe, user=user)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_recipe():
    """Add a new recipe."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        ingredients_raw = request.form.get("ingredients", "")
        instructions_raw = request.form.get("instructions", "")

        ingredients = [i.strip() for i in ingredients_raw.split("\n") if i.strip()]
        instructions = [i.strip() for i in instructions_raw.split("\n") if i.strip()]

        if name:
            recipes_collection.insert_one(
                {
                    "name": name,
                    "description": description,
                    "ingredients": ingredients,
                    "instructions": instructions,
                    "author_id": current_user.id
                }
            )
        return redirect(url_for("home"))

    return render_template("add.html")


@app.route("/edit/<recipe_id>", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    """Edit an existing recipe."""
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe or recipe.get("author_id") != current_user.id:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        prep_time = request.form.get("prep_time", "").strip()
        ingredients_raw = request.form.get("ingredients", "")
        instructions_raw = request.form.get("instructions", "")

        ingredients = [i.strip() for i in ingredients_raw.split("\n") if i.strip()]
        instructions = [i.strip() for i in instructions_raw.split("\n") if i.strip()]

        recipes_collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {
                "$set": {
                    "name": name,
                    "description": description,
                    "prep_time": prep_time,
                    "ingredients": ingredients,
                    "instructions": instructions,
                }
            },
        )
        return redirect(url_for("view_recipe", recipe_id=recipe_id))

    return render_template("edit.html", recipe=recipe)


@app.route("/delete/<recipe_id>", methods=["GET", "POST"])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe – shows confirmation page on GET, deletes on POST."""
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe or recipe.get("author_id") != current_user.id:
        return redirect(url_for("home"))

    if request.method == "POST":
        recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
        return redirect(url_for("home"))

    return render_template("delete.html", recipe=recipe)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    results = []
    query = ""
    include_ingredients = ""
    exclude_ingredients = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        include_ingredients = request.form.get("include_ingredients", "").strip()
        exclude_ingredients = request.form.get("exclude_ingredients", "").strip()

        filters = {}

        # Name search
        if query:
            filters["name"] = {"$regex": query, "$options": "i"}

        # Include ingredients filter
        if include_ingredients:
            include_list = [i.strip() for i in include_ingredients.split(",") if i.strip()]
            filters["ingredients"] = {
                "$all": [{"$elemMatch": {"$regex": term, "$options": "i"}} for term in include_list]
            }

        results = list(recipes_collection.find(filters))

        # Exclude ingredients
        if exclude_ingredients:
            exclude_list = [e.strip().lower() for e in exclude_ingredients.split(",") if e.strip()]
            results = [
                r for r in results
                if not any(
                    any(excl in ing.lower() for excl in exclude_list)
                    for ing in r.get("ingredients", [])
                )
            ]

    return render_template("search.html", results=results, query=query,
                           include_ingredients=include_ingredients,
                           exclude_ingredients=exclude_ingredients)

@app.route("/save/<recipe_id>", methods=["POST"])
@login_required
def save_recipe(recipe_id):
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$addToSet": {"saved_recipes": ObjectId(recipe_id)}}
    )

    return redirect(request.referrer or url_for("profile"))

@app.route("/unsave/<recipe_id>", methods=["POST"])
@login_required
def unsave_recipe(recipe_id):
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"saved_recipes": ObjectId(recipe_id)}}
    )
    return redirect(request.referrer or url_for("profile"))

@app.context_processor
def inject_saved_ids():
    if current_user.is_authenticated:
        user = db.users.find_one({"_id": ObjectId(current_user.id)})
        return {"current_user_saved_ids": user.get("saved_recipes", [])}
    return {"current_user_saved_ids": []}

@app.route("/rate/<recipe_id>", methods=["POST"])
@login_required
def rate_recipe(recipe_id):
    rating = request.form.get("rating")
    if rating:
        rating = int(rating)
        recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        ratings = recipe.get("ratings", {})
        ratings[str(current_user.id)] = rating  # overwrites if already rated
        avg = round(sum(ratings.values()) / len(ratings), 1)
        recipes_collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": {"ratings": ratings, "avg_rating": avg}}
        )
    return redirect(url_for("view_recipe", recipe_id=recipe_id))
    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)