# TripSplit

TripSplit is a shared expense management application built with two independent Flask microservices. Users can create groups, add participants, record shared expenses, calculate balances, and register settlement payments.

The project demonstrates microservice architecture, database migrations, API integration, automated testing, containerization, and cloud deployment.

## Features

### Expense Service
- Create and manage expense groups
- Add participants to groups
- Record shared expenses
- Select participants sharing each expense
- Retrieve group expense snapshots

### Settlement Service
- Calculate participant balances
- Retrieve group balances
- Record payments between participants
- Communicate with the Expense Service through its API

### Additional Features
- Independent databases for each service
- SQL Server persistence
- Database migrations
- Request logging and health endpoints
- CORS configuration
- Responsive static UI
- Automated tests and coverage reporting

## Architecture

TripSplit consists of three main components:

- **Frontend:** Static HTML, CSS and JavaScript hosted through Azure Storage Static Website. The browser calls both service APIs.
- **Expense Service:** Flask API responsible for groups, participants, expenses and expense shares.
- **Settlement Service:** Flask API responsible for balance calculations and settlement records. It calls the Expense Service snapshot endpoint over HTTP to calculate balances.

Each service owns its own database. Docker Compose runs both databases on one local SQL Server instance. In Azure, each service connects to its own Azure SQL database.

## Tech Stack

- Python 3.11
- Flask
- Microsoft SQL Server 2022 locally
- Azure SQL in deployment
- pyodbc and ODBC Driver 18
- HTML, CSS and JavaScript
- Docker and Docker Compose
- Azure Container Apps
- Azure Storage Static Website Hosting
- GitHub Actions
- GitHub Container Registry
- pytest, pytest-cov and Ruff
- OpenAPI

## Project Structure

```text
TripSplit-app/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── db/
│   └── init/                Local database and login initialization
├── services/
│   ├── expense-service/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   ├── migration_runner.py
│   │   └── openapi.yaml
│   └── settlement-service/
│       ├── migrations/
│       ├── tests/
│       ├── Dockerfile
│       ├── app.py
│       ├── migration_runner.py
│       └── openapi.yaml
├── ui/                     Static frontend and local Nginx configuration
├── evidence/               Azure migration evidence
├── docker-compose.yml
├── system.schema.json
├── system.yaml
├── ADR.md
├── AI_USAGE.md
└── README.md
```

## Local Setup

### Requirements
- Python 3.11
- Docker Desktop with Docker Compose
- Git

On Apple Silicon, enable Rosetta emulation in Docker Desktop for the `linux/amd64` SQL Server image.

### Run with Docker Compose

Clone the repository:

```bash
git clone https://github.com/dakoalesia1-boop/TripSplit-app.git
cd TripSplit-app
```

Create a `.env` file in the repository root. Replace each placeholder with a different strong local password. The SQL Server administrator password must meet SQL Server's password complexity requirements. Keep `.env` out of Git.

```dotenv
SQLSERVER_SA_PASSWORD=replace_with_local_admin_password
EXPENSE_DB_PASSWORD=replace_with_local_expense_password
SETTLEMENT_DB_PASSWORD=replace_with_local_settlement_password
```

Build and start the stack:

```bash
docker compose up --build
```

The application will be avaliable at:
- Frontend: http://localhost:8080
- Expense Service health: http://localhost:8000/health
- Settlement Service health: http://localhost:8001/health

To stop the application:

```bash
docker compose down
```
## Run the Expense Service by itself

```bash
docker compose up --build expense-service
```

## API Documentation

- [Expense Service OpenAPI specification](services/expense-service/openapi.yaml)
- [Settlement Service OpenAPI specification](services/settlement-service/openapi.yaml)
- [System configuration](system.yaml) and [validation schema](system.schema.json)

## Testing

From the repository root, activate a Python 3.11 virtual environment and install the dependencies:

```bash
python -m pip install -r services/expense-service/requirements.txt
python -m pip install -r services/settlement-service/requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install ruff==0.11.13
```
Run the lint check and each service's test suite with the coverage thresholds used in CI:

```bash
python -m ruff check services/
python -m pytest --cov=expense_service_app --cov-report=term-missing --cov-fail-under=70 services/expense-service/tests
python -m pytest --cov=settlement_service_app --cov-report=term-missing --cov-fail-under=70 services/settlement-service/tests
```

## Azure Deployment
The live frontend is available at [TripSplit on Azure](https://adakoieu2024ui.z1.web.core.windows.net/).

Azure Container Apps hosts the Expense and Settlement services. Each connects to its own Azure SQL database. Azure Storage serves the static frontend.

On a push to `main`, GitHub Actions runs CI for that commit and publishes images tagged with its Git SHA to GitHub Container Registry. The CD workflow updates both Container Apps with those images, generates the frontend configuration with the deployed API URLs, uploads the static files to the storage account's `$web` container, and checks both deployed health endpoints.


The deployment pipeline runs CI checks and publishes container images before deploying the services and uploading the frontend.

## Configuration and Security

Database connection strings and passwords are stored as Azure Container Apps secrets and GitHub repository secrets. Credentials are not included in the repository.

The project configuration is documented in system.yaml and validated against system.schema.json.

For architectural decisions, see ADR.md. For details about AI assistance, see AI_USAGE.md.

## AI Disclosure Statement

I acknowledge the use of Claude and ChatGPT to assist with project planning, microservices architecture, Docker configuration, Azure deployment, CI/CD pipeline setup, debugging, testing suggestions, and documentation.

The prompts used included requests for guidance on containerizing the Expense and Settlement services, configuring Docker Compose, deploying services to Azure Container Apps, setting up Azure SQL databases and Azure Storage static website hosting, configuring GitHub Actions workflows, and troubleshooting deployment issues.

The generated output was reviewed, tested, modified, and integrated into the final implementation. A detailed record of AI assistance is available in `AI_USAGE.md`.