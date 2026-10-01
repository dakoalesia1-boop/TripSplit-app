# TripSplit

TripSplit is a lightweight shared expense tracking application built with Flask and SQLite. The application allows users to create groups, add participants, track expenses, calculate balances, and record settlement payments.

The project emphasizes modular backend design, testing, process documentation, and deployment readiness.

---

## Features

### Expense Management Domain
- Create expense groups
- Add participants to groups
- Add shared expenses
- Select which participants shared an expense
- Track total spending and expense counts

### Settlement Domain
- Calculate participant balances
- Display settlement summaries
- Record settlement payments
- View settlement history

### Additional Features
- SQLite persistence
- Bootstrap based responsive UI
- Modular service layer architecture
- Automated unit testing with pytest

---

## Tech Stack

- Python 3
- Flask
- SQLAlchemy
- SQLite
- Bootstrap 5
- pytest
- pytest-cov

---

## Project Structure

```text
TripSplit-app/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── static/
│   └── templates/
│
├── tests/
├── docs/
├── data/
│
├── ADR.md
├── AI_USAGE.md
├── requirements.txt
├── run.py
└── README.md

## Setup Instructions
1. Clone the repository
git clone <repository-url>
cd TripSplit-app

2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies 
pip install -r requirements.txt

## Running the Application
python run.py
http://localhost:5000

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| PORT | Flask application port | 5000 |
| DATA_DIR | SQLite database directory | data |
| SECRET_KEY | Flask secret key | dev-secret-key |

## Database
The application automatically creates the SQLite database on startup with a default database location at data/tripsplit.db.

## Running Tests

### Run unit tests
pytest

### Run coverage report
pytest --cov=app

Testing primarly targets the settlement calculations, shared expense logic, participant balance calculations and expense sharing rules.

## Deployment Requirements
The application runs as a single Flask process. It uses SQLite persistance and binds to 0.0.0.0. It reads the port from environment variables, requires no external database and starts with a single command. 

## AI Disclosure Statement
I acknowledge the use of ChatGPT to assist with project planning, architecture guidance, debugging, testing suggestions, and documentation support. The prompts used included requests for Flask project structure guidance, SQLAlchemy schema design, settlement calculation logic, and testing strategies. The generated output was reviewed, modified, and integrated into the final implementation. A full documentation is found under AI_USAGE.md.