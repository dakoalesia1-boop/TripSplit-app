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
