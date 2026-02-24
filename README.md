# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Let Them Cook is an app for cooks to share their recipes, and take and rate other cooks' recipes.

## User stories

User Stories: [GitHub Issues Page](https://github.com/swe-students-spring2026/2-web-app-citrus_cyclones/issues)

## Steps necessary to run the software

1. Clone the repository and open it in VS Code.
2. Install pipenv (if not already installed):
	- `pip install pipenv`
3. Activate the virtual environment and install dependencies:
	- `pipenv shell`
	- `pipenv install`
4. Create `.env` from `env.example`.
5. For a guaranteed local demo (no MongoDB required), set in `.env`:
	- `DEMO_MODE=true`
6. Run the app:
	- `python app.py`
7. Open:
	- `http://127.0.0.1:5000`
8. Exit the virtual environment when done:
	- `exit`

Notes:
- If you want to use a real MongoDB database, set `DEMO_MODE=false` and provide a valid `MONGO_URI`.
- If MongoDB is unreachable, the app automatically falls back to in-memory demo data.

## Task boards

- Sprint 1: [GitHub Taskboard](https://github.com/orgs/swe-students-spring2026/projects/40)
- Sprint 2: [GitHub Taskboard]()