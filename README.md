# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Let Them Cook is an app for cooks to share their recipes, and take and rate other cooks' recipes.

## User stories

User Stories: [GitHub Issues Page](https://github.com/swe-students-spring2026/2-web-app-citrus_cyclones/issues?q=is%3Aissue%20state%3Aclosed%20project%3Aswe-students-spring2026%2F40)

## Steps necessary to run the software

1. Clone the repository and open it in VS Code.
2. Install pipenv (if not already installed):
	- `pip install pipenv`
3. Activate the virtual environment and install dependencies:
	- `pipenv shell`
	- `pipenv install`
4. Create `.env` from `env.example` and set your MongoDB connection:
	- `MONGO_URI` — your MongoDB connection string
	- `MONGO_DBNAME` — database name, defaults to `let_them_cook`
5. Seed the database with sample users and recipes (optional but recommended for local development):
	- `python scripts/seed_db.py`
	- Uses `data/users.json` and `data/sample_recipes.json`; ensure these files exist.
6. Run the app:
	- `python app.py`
7. Open:
	- `http://127.0.0.1:5000`
8. Exit the virtual environment when done:
	- `exit`

Notes:
- The seed script requires a running MongoDB instance and a valid `MONGO_URI`. Run it after the database is available to load sample data.

## Task boards

- Sprint 1: [GitHub Taskboard](https://github.com/orgs/swe-students-spring2026/projects/40)
- Sprint 2: [GitHub Taskboard](https://github.com/orgs/swe-students-spring2026/projects/47)