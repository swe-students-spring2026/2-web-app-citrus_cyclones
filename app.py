import os
from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "dev" # change this to an environment variable later

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
        })

        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


def _is_truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

# ---------------------------------------------------------------------------
# MongoDB connection with timeout fallback
# If the remote MongoDB Atlas cluster is unreachable (timeout), we fall back
# to an in-memory database powered by mongomock so the app runs locally.
# ---------------------------------------------------------------------------
SAMPLE_RECIPES = [
    {
        "name": "Spaghetti Bolognese",
        "description": "Classic Italian pasta with a rich and savory meat sauce. A family favorite that is easy to make and always delicious.",
        "ingredients": [
            "400g spaghetti", "500g ground beef", "1 can crushed tomatoes",
            "1 onion diced", "3 cloves garlic minced", "2 tbsp olive oil",
            "Salt and pepper to taste", "Fresh basil",
        ],
        "instructions": [
            "Boil spaghetti in salted water until al dente",
            "Heat olive oil and saute onion and garlic",
            "Add ground beef and brown",
            "Pour in crushed tomatoes and simmer for 20 min",
            "Season with salt, pepper, and basil",
            "Serve sauce over spaghetti",
        ],
    },
    {
        "name": "Chicken Stir Fry",
        "description": "Quick and healthy chicken stir fry with colorful vegetables and a savory soy-ginger sauce.",
        "ingredients": [
            "2 chicken breasts sliced", "1 bell pepper", "1 cup broccoli",
            "2 carrots sliced", "3 tbsp soy sauce", "1 tbsp ginger grated",
            "2 tbsp sesame oil", "Rice for serving",
        ],
        "instructions": [
            "Slice chicken and vegetables",
            "Heat sesame oil in a wok over high heat",
            "Cook chicken until golden",
            "Add vegetables and stir fry 3-4 minutes",
            "Pour soy sauce and ginger, toss to coat",
            "Serve over steamed rice",
        ],
    },
    {
        "name": "Chocolate Chip Cookies",
        "description": "Soft and chewy chocolate chip cookies that are perfect for dessert or a snack.",
        "ingredients": [
            "2 1/4 cups flour", "1 cup butter softened", "3/4 cup sugar",
            "3/4 cup brown sugar", "2 eggs", "1 tsp vanilla extract",
            "1 tsp baking soda", "2 cups chocolate chips",
        ],
        "instructions": [
            "Preheat oven to 375F",
            "Cream butter and sugars together",
            "Beat in eggs and vanilla",
            "Mix in flour and baking soda",
            "Fold in chocolate chips",
            "Drop spoonfuls onto baking sheet",
            "Bake 9-11 minutes until golden",
        ],
    },
    {
        "name": "Caesar Salad",
        "description": "Crisp romaine lettuce with creamy Caesar dressing, croutons, and parmesan cheese.",
        "ingredients": [
            "1 head romaine lettuce", "1/2 cup Caesar dressing",
            "1 cup croutons", "1/4 cup grated parmesan",
            "1 lemon juiced", "Salt and pepper",
        ],
        "instructions": [
            "Wash and chop romaine lettuce",
            "Toss lettuce with Caesar dressing",
            "Add croutons and parmesan",
            "Squeeze lemon juice over salad",
            "Season with salt and pepper",
            "Serve immediately",
        ],
    },
    {
        "name": "Banana Pancakes",
        "description": "Fluffy banana pancakes that make for a perfect weekend breakfast.",
        "ingredients": [
            "2 ripe bananas", "2 eggs", "1 cup flour",
            "1/2 cup milk", "1 tsp baking powder",
            "1 tbsp sugar", "Butter for cooking", "Maple syrup",
        ],
        "instructions": [
            "Mash bananas in a large bowl",
            "Whisk in eggs and milk",
            "Add flour, baking powder, and sugar; mix until smooth",
            "Heat butter in a pan over medium heat",
            "Pour batter and cook until bubbles form, then flip",
            "Serve with maple syrup",
        ],
    },
]


def _connect_db():
    """Use in-memory DB in demo mode; otherwise try MongoDB then fall back."""
    mongo_uri = os.getenv("MONGO_URI", "")
    mongo_dbname = os.getenv("MONGO_DBNAME", "let_them_cook")
    demo_mode = _is_truthy(os.getenv("DEMO_MODE", "true"))

    if demo_mode:
        import mongomock

        mock_client = mongomock.MongoClient()
        db = mock_client[mongo_dbname]
        if db.recipes.count_documents({}) == 0:
            db.recipes.insert_many(SAMPLE_RECIPES)
            print(f" * Demo mode enabled. Seeded {len(SAMPLE_RECIPES)} recipes in memory.")
        return db

    # --- attempt real MongoDB connection --------------------------------
    if mongo_uri:
        try:
            from pymongo import MongoClient

            client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=5000,
            )
            client.server_info()  # force connection check
            db = client[mongo_dbname]
            print(" * Connected to MongoDB Atlas successfully.")
            return db
        except Exception as exc:
            print(f" * MongoDB unreachable ({exc}). Falling back to in-memory DB.")

    # --- fallback: in-memory mongomock ----------------------------------
    import mongomock

    mock_client = mongomock.MongoClient()
    db = mock_client[mongo_dbname]
    # Seed sample data so there is something to show
    if db.recipes.count_documents({}) == 0:
        db.recipes.insert_many(SAMPLE_RECIPES)
        print(f" * Seeded {len(SAMPLE_RECIPES)} sample recipes into in-memory DB.")
    return db


db = _connect_db()
recipes_collection = db.recipes


# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------

@app.route("/")
@login_required
def home():
    """Display all recipes on the home page."""
    recipes = list(recipes_collection.find())
    return render_template("home.html", recipes=recipes)


@app.route("/create-recipe", methods=["GET", "POST"])
@login_required
def create_recipe():
    """Create a new recipe."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
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
                    "ingredients": ingredients,
                    "prep_time": int(prep_time) if prep_time else None,
                    "instructions": instructions,
                }
            )
        return redirect(url_for("home"))

    return render_template("create_recipe.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/recipe/<recipe_id>")
@login_required
def view_recipe(recipe_id):
    """View a single recipe's details."""
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
    return render_template("recipe.html", recipe=recipe)


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
                }
            )
        return redirect(url_for("home"))

    return render_template("add.html")


@app.route("/edit/<recipe_id>", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    """Edit an existing recipe."""
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
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

    if request.method == "POST":
        recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
        return redirect(url_for("home"))

    return render_template("delete.html", recipe=recipe)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for recipes by name."""
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "")
        # Search by recipe name (case-insensitive)
        results = list(
            recipes_collection.find(
                {"name": {"$regex": query, "$options": "i"}}
            )
        )

    return render_template("search.html", results=results, query=query)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)