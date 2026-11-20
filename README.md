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
- Responsive web interface
- Automated tests and coverage reporting

## Architecture

TripSplit consists of three main components:

- **Frontend:** Static HTML, CSS and JavaScript hosted through Azure Storage Static Website.
- **Expense Service:** Flask API responsible for groups, participants and expenses.
- **Settlement Service:** Flask API responsible for balance calculations and settlement records.

The Settlement Service retrieves expense information from the Expense Service through its HTTP API. Each backend service has its own Azure SQL database.

## Tech Stack

- Python 3.11
- Flask
- Microsoft SQL Server / Azure SQL
- pyodbc and ODBC Driver 18
- HTML, CSS and JavaScript
- Docker and Docker Compose
- Azure Container Apps
- Azure Storage Static Website
- GitHub Actions
- GitHub Container Registry
- pytest and pytest-cov
- OpenAPI

## Project Structure

```text
TripSplit-app/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
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
├── ui/
│   ├── app.js
│   ├── config.js
│   ├── index.html
│   ├── nginx.conf
│   └── style.css
├── docker-compose.yml
├── system.schema.json
├── system.yaml
├── ADR.md
├── AI_USAGE.md
└── README.md

## Local Setup

### Requirements
- Python 3.11
- Docker Desktop
- Git

### Run with Docker Compose

Clone the repository:

```bash
git clone https://github.com/dakoalesia1-boop/TripSplit-app.git
cd TripSplit-app

Build and start the application:

```bash
docker compose up --build

The application will be avaliable at:
- Frontend: http://localhost:8080
- Expense Service: http://localhost:8000
- Settlement Service: http://localhost:8001

To stop the application:

```bash
docker compose down

## API Documentation

OpenAPI specifications are available in:

- services/expense-service/openapi.yaml
- services/settlement-service/openapi.yaml

Both services provide a /health endpoint.

## Testing

Run the tests using the project's development dependencies:

```bash
pip install -r requirements-dev.txt
pytest

## Azure Deployment
The application is deployed using:

- Azure Container Apps for the Expense and Settlement services.

- Azure SQL databases, with a separate database for each service.

- Azure Storage Static Website for the frontend.

- GitHub Container Registry for Docker images.

- GitHub Actions for continuous integration and deployment.

The frontend is available at:

https://adakoieu2024ui.z1.web.core.windows.net/

The deployment pipeline runs CI checks and publishes container images before deploying the services and uploading the frontend.

## Configuration and Security

Database connection strings and passwords are stored as Azure Container Apps secrets and GitHub repository secrets. Credentials are not included in the repository.

The project configuration is documented in system.yaml and validated against system.schema.json.

For architectural decisions, see ADR.md. For details about AI assistance, see AI_USAGE.md.
## AI Disclosure Statement

I acknowledge the use of Claude and ChatGPT to assist with project planning, microservices architecture, Docker configuration, Azure deployment, CI/CD pipeline setup, debugging, testing suggestions, and documentation.

The prompts used included requests for guidance on containerizing the Expense and Settlement services, configuring Docker Compose, deploying services to Azure Container Apps, setting up Azure SQL databases and Azure Storage static website hosting, configuring GitHub Actions workflows, and troubleshooting deployment issues.

The generated output was reviewed, tested, modified, and integrated into the final implementation. A detailed record of AI assistance is available in `AI_USAGE.md`.