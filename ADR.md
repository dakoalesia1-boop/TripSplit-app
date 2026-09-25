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
