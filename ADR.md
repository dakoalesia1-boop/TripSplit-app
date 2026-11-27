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

## 7. Database Ownership and Migration Strategy

Date: 2026-11-13 (updated 2026-11-26)

Status: Decided

Context:
After splitting TripSplit into two backend services, each service needs persistent storage without creating unnecessary coupling between the domains. Schema changes must also be applied safely to existing Azure SQL data during deployment.

Decision:
Each service has its own SQL Server database. The Expense Service owns expense-related data, while the Settlement Service owns settlement records. Each service manages its schema through its own SQL migration scripts and migration runner.

Migrations are versioned SQL files and are recorded in a `schema_migrations` table. The migration runner checks this table and applies only migrations that have not already been recorded. This prevents previously applied migrations from being run again during subsequent container starts.

Settlement records store `group_id`, `payer_id`, and `receiver_id` as IDs from the Expense Service. Splitting the databases removed the ability to enforce group and participant references with foreign keys across the two services. When creating a settlement, the Settlement Service checks that the payer and receiver IDs are positive and different and that the amount is positive and finite. It does not verify that those IDs belong to the group before saving. When calculating balances, it reads group, participant, and expense data through the Expense Service snapshot endpoint. A settlement can therefore contain a reference that was never validated against the Expense database.

Migration 003 (`003_add_expense_created_at.sql`) adds a non-null `created_at` column to the Expense Service's `expenses` table, using `SYSUTCDATETIME()` as its default. This provides a timestamp for existing rows when the migration is applied and for new rows inserted afterwards. Existing timestamps represent migration-time values, not the original dates on which those expenses were created. The Expense Service snapshot API also exposes this timestamp.

Alternatives considered:
Using one shared database was considered, but it would create stronger coupling between the services. Managing all migrations from a central script was also considered, but separate migration runners provide clearer ownership. Rebuilding the database or recreating the expenses table was rejected because it could destroy existing records.

Consequences:
Each service can manage its own database schema and migrations independently. The migration history provides a record of applied changes, and forward-only migrations reduce the risk of losing existing data. Migration changes still require testing and verification against the deployed database. Before and after database evidence is retained to demonstrate that existing expense records remain present.

Recovery:
Before applying a potentially risky production migration, preserve a suitable database backup or recovery point. If a migration fails, inspect the database state and deployment logs before retrying. Prefer a corrective forward migration to repair an applied schema change. Do not delete migration-history records or manually reverse schema changes as a routine recovery method. If the deployment fails, investigate and correct the cause before deploying again; preserve the existing database records.

---

## 8. Serverless Hosting on Azure

Date: 2026-11-17 (Updated 2026-11-27)

Status: Decided

Context:
TripSplit needs public HTTPS endpoints for the two Flask services, a place to serve the static UI, and a separate database for each service. Traffic is expected to be intermittent, so idle compute matters.

Decision:
Deploy Expense Service and Settlement Service to Azure Container Apps on the Consumption plan. Each service uses its own Azure SQL Database on the serverless tier. Azure Storage static website hosting serves the UI. GitHub Container Registry stores the service images, and GitHub Actions authenticates to Azure with OpenID Connect and a federated managed identity. The target is zero minimum and one maximum replica per service. A single replica limits concurrent startup migrations within a revision. Each service applies its own pending migrations and checks its own database. When Azure SQL is paused, the connection retry and backoff give it time to resume.

Alternatives considered:
An always-on hosting plan would reduce cold starts but incur idle compute costs. Serving the UI from another application container would add a deployment and runtime for files that Azure Storage can serve directly.

Consequences:
A request after an idle period can take longer or receive a temporary error while the service starts and SQL resumes. The post-deploy health check retries to allow for startup. Container Apps and Azure SQL use consumption-based compute, while Storage usage and retained logs are separate resources. At 100 times the traffic, I would measure cold-start latency and SQL load before changing replica limits. Before adding replicas, I would move migration execution to a controlled deployment step or serialize it with a database lock.

---

## 9. Pipeline and Testing

Date: 2026-11-18 (Updated 2026-11-27)

Status: Decided

Context:
The service split adds failure modes that unit tests alone cannot cover. A change can pass mocked tests but still fail to build, initialize SQL Server, apply migrations, or start on Azure.

Decision:
GitHub Actions runs Ruff against `services/`, validates the two OpenAPI documents and `system.yaml`, runs the service test suites, and enforces a 70% coverage minimum for each service. The SQL Server startup job uses Docker Compose and a fresh SQL Server 2022 instance on the runner. `db-init` creates the two databases and their logins, each service runs its migrations on startup, and the job checks both `/health` responses for `status: ok` and `db: ok`. The image build job depends on both the backend test job and the SQL Server startup job.

The cross-service tests cover the Settlement Service's dependency on the Expense Service snapshot endpoint. The settlement balance calculation uses the group and expense data returned by that endpoint. The suite also checks that an unavailable Expense Service produces a controlled `502` response.

On a push to `main`, CD runs CI for that commit, publishes images tagged with its Git SHA, deploys both services, uploads the static UI with its production configuration, and checks the deployed health endpoints.

Alternatives considered:
Using only mocked tests would keep CI fast but would miss problems such as the ODBC installer failing on the runner's architecture. Running CI against Azure SQL would tie branch checks to the deployed databases. The disposable SQL Server instance keeps CI isolated from those databases.

Consequences:
The SQL Server job adds runtime but catches database initialization and startup failures before deployment. Live browser flows and Azure specific cold start behavior are checked separately because the local runner does not reproduce those conditions.

---

## 10. Message Broker Left Out

Date: 2026-11-20 (Updated 2026-11-27)

Status: Decided

Context:
The Settlement Service needs current expense and participant data when a user requests balances. The Expense Service owns those records and exposes the required data through its snapshot endpoint.

Decision:
Keep the synchronous HTTP request from Settlement Service to Expense Service. Use a bounded timeout and return a clear error when the snapshot cannot be retrieved.

Alternatives considered:
A message broker could deliver expense events asynchronously and allow the Settlement Service to maintain a local copy. That approach would also require handling retries, duplicate events, stale data, and rebuilding state from events.

Consequences:
The balance request depends on the Expense Service being reachable, but both services retain ownership of their data and can report their own database health independently. I would revisit a broker if TripSplit needed background processing, multiple consumers of expense events, or replay after outages.
