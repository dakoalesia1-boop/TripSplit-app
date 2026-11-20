## 1. Backend Language and Framework Choice
Date: 2026-09-25

Status: Decided

Context:
The application requires a lightweight backend framework capable of handling routing, SQLite integration, and server-side rendering while remaining easy to understand and maintain for a small monolithic project.

Decision:
Python with Flask was chosen because it provides a simple structure, integrates well with SQLite and SQLAlchemy, and minimizes unnecessary complexity for this assignment.

Alternatives considered:
Django was another option, but it was rejected since its built-in features would add unnecessary complexity for a small application. Node.js with Express was also considered, but Python was chosen since it is more familiar and it has easier testing with pytest.

Consequences:
The project remains lightweight and easier to explain during the comprehension check. However, Flask requires more manual project structure decisions compared to Django.

## 3. SQLite Schema Design and Relationships
Date: 2026-09-27

Status: Decided

Context:
The application requires persistent storage for groups, participants, and shared expenses while keeping the data structure simple for a lightweight monotholic application. The schema also needs to support future calculations and possible modular separation of domains.

Decisions:
I decided to create separate tables for groups, participants, and expenses using forgien key relationships. Expenses belong to a specific group and reference the participant who paid. Participants who are linked to groups through a one-to-many relationship.

Alternatives considered:
Another option was to use a imple single-table structure, but this would duplicate participant and group information across expense records and make calculations harder to maintain.

Concequences:
The schema is easier to extend later for features such as settlement tracking and analytics. But the schema also requires additional joins and relationship handling in the application logic.

## 2. Modular Separation of Feature Domains
Date: 2026-09-29

Status: Decided

Context:
The application requires at least two backend feature domains that could later be separated into independent services. The project also needs business logic that remains maintainable and testable as functionality grows.

Decision:
The application was divided into an Expense Management domain and a Settlement Calculation domain. Expense management handles creating groups, participants, and expenses through Flask routes and database models, while settlement calculations were moved into a dedicated service module responsible for balance computation.

Alternatives considered:
I considered keeping all calculation logic directly inside Flask route handlers but this would tightly couple business logic with HTTP request handling and make testing more difficult.

Consequences:
The service layer approach improves modularity and makes settlement calculations easier to test independently from the web framework. However, it introduces additional project structure and abstraction compared to a smaller single file Flask application.

## 4. Testing Strategy and Coverage Priorities
Date: 2026-09-30

Status: Decided

Context:
The project requires automated tests with at least 70% coverage focused on core business logic. The application contains both Flask routing code and financial settlement calculations.

Decision:
Testing efforts were focused primarily on the settlement calculation service because it contains the application's most important business logic. Unit tests were written to validate balance calculations, participant inclusion rules, and expense sharing behavior independently from Flask routes and templates. Both pytest and pytest --cov=app passed with 100%.

Alternatives considered:
I considered testing full Flask routes and HTML rendering more extensively, but since the assignment emphasizes core logic rather than framework behavior, this option was not seen as important.

Consequences:
The testing strategy provides strong confidence in the financial calculation logic and supports easier debugging of settlement behavior. However, some UI and route integration behavior receives lighter automated coverage.

## 5. Features Deliberately Excluded
Date: 2026-10-01

Status: Decided

Context:
The project scope needed to remain manageable within the assignment timeline while maintaining focus on modular backend logic and testing quality.

Decision:
User authentication, external payment APIs, and real-time synchronization were intentionally excluded from the application.

Alternatives considered:
Authentication and payment integration were considered to improve realism but rejected because they would add significant complexity without contributing meaningfully to the core financial logic or assignment requirements.

Consequences:
The project remains focused on expense sharing functionality, modularity, and testability. However, the application would require additional security and user management features before being production ready.

## 6. Service Split and Cross-Service Boundary
Date: 2026-11-11

Status: Decided

Context:
Assignment 2 requires splitting the TripSplit monolith into separate services along the seam defined in Assignment 1. The project needs a clear division of responsibility between the two feature domains while keeping the system containerized and manageable.

Decision:
The application was split into two services: an Expense Service and a Settlement Service. The Expense Service owns groups, participants, expenses, expense shares, and categories. The Settlement Service owns settlement records and balance calculations, and it reads expense data from the Expense Service over HTTP when it needs to compute balances. The UI is kept static and calls both services from the browser.

Alternatives considered:
Keeping the application as one backend with a shared database was considered, but rejected because it would not satisfy the assignment requirement to split the seam into separate services. Splitting the UI into a third backend service was also considered unnecessary because the assignment specifically requires two services, not three.

Consequences:
The domains are now independently deployable and easier to reason about, but the Settlement Service depends on the Expense Service being available for cross-service data access. This adds HTTP communication, failure handling, and more deployment complexity compared to the original monolith.

**## 7. Database Ownership and Migration Strategy**

Date: 2026-11-13

Status: Decided

Context:
After splitting TripSplit into two backend services, each service needs persistent storage without creating unnecessary coupling between the domains.

Decision:
Each service was given its own SQL Server database. The Expense Service manages its own expense-related data, while the Settlement Service manages settlement records. Database schema changes are handled through separate migration scripts and migration runners inside each service.

Alternatives considered:
Using one shared database was considered, but it would create stronger coupling between the services. Managing all migrations from a central script was also considered, but separate migration runners provide clearer ownership.

Consequences:
Each service can manage its own database schema and migrations independently. However, maintaining two databases introduces additional configuration and deployment requirements.

---

**## 8. REST API Communication Between Services**

Date: 2026-11-17

Status: Decided

Context:
The Settlement Service needs access to expense and participant information to calculate balances. Since the services have separate databases, they need a communication mechanism that does not require direct database access across service boundaries.

Decision:
REST APIs were implemented for both services. The Settlement Service retrieves the required group and expense information from the Expense Service through HTTP requests using a dedicated snapshot endpoint.

Alternatives considered:
Direct database access from the Settlement Service was considered, but rejected because it would violate service ownership. A shared database or message broker was also considered unnecessary for the current application requirements.

Consequences:
The services remain independent and communicate through defined API endpoints. However, settlement calculations depend on the Expense Service being available, so request timeouts and error handling are necessary.

---

**## 9. Containerized Deployment and Static Frontend Architecture**

Date: 2026-11-18

Status: Decided

Context:
The application needs a consistent way to run the frontend and backend services together during development while keeping the frontend separate from backend business logic.

Decision:
Docker Compose was used to run the frontend, Expense Service, Settlement Service, and database environment together. The frontend remains a static application served through Nginx and communicates directly with the two backend APIs.

Alternatives considered:
Running each service manually was considered, but it would require more setup and make local development less consistent. Moving the frontend into a separate backend framework was also considered unnecessary.

Consequences:
The application can be started and tested using one Docker Compose configuration. The services remain independently containerized, although the setup requires Docker and additional container configuration.

---

**## 10. Azure Deployment and Automated CI/CD**

Date: 2026-11-20

Status: Decided

Context:
The application needs to be deployed to Azure, with automated testing and deployment to reduce manual configuration and make future updates easier.

Decision:
Azure Container Apps was selected to host the Expense and Settlement services, with a separate Azure SQL database for each service. Azure Storage Static Website hosting was selected for the frontend. GitHub Actions is used for CI/CD, with container images published to GitHub Container Registry and Azure authentication configured through OpenID Connect using a federated managed identity.

Alternatives considered:
Deploying the services manually was considered, but rejected because it would make updates more difficult to reproduce. Hosting the frontend inside a backend container was also considered, but Azure Storage provides a simpler solution for static files.

Consequences:
The application has a repeatable deployment process, separate hosting for the frontend and backend, and automated checks before deployment. However, the setup introduces additional cloud resources, permissions, secrets, and configuration that need to be maintained.