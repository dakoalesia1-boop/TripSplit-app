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