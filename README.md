# Secure E-Voting API (Backend)

This project is a secure, blockchain-inspired electronic voting system backend. It has been re-architected to follow **Clean Architecture** principles, ensuring scalability, maintainability, and high testability.

## 🏗 Architecture

The project follows a **Modular Monolith** approach using **Clean Architecture**. The codebase is organized into four concentric layers, decoupling business logic from external frameworks and databases.

### Layer Structure (`src/`)

1.  **Domain (`src/domain/`)** - *The Core*
    *   Contains the enterprise business rules and **Interfaces (Protocols)**.
    *   **Dependencies:** None. Pure Python.
    *   *Example:* `IUserRepository`, `IElectionRepository`.

2.  **Application (`src/application/`)** - *Use Cases*
    *   Contains **Services** that orchestrate the business logic using the domain interfaces.
    *   Contains **DTOs (Schemas)** for data transfer.
    *   **Dependencies:** Domain layer.
    *   *Example:* `ElectionService` (Logic for creating elections), `VotingService` (Logic for casting votes).

3.  **Infrastructure (`src/infrastructure/`)** - *Adapters*
    *   Implements the interfaces defined in the Domain layer.
    *   Handles Database (SQLAlchemy), Security (JWT, Hashing), and other external tools.
    *   **Dependencies:** Application & Domain layers.
    *   *Example:* `SqlAlchemyElectionRepository`, `database/models.py`, `database/seeder.py`.

4.  **Presentation (`src/presentation/`)** - *Entry Point*
    *   Handles HTTP requests (FastAPI Routers) and Dependency Injection wiring.
    *   **Dependencies:** Application & Infrastructure layers.
    *   *Example:* `api/v1/election_router.py`.

---

##  Features

*   **Secure Authentication:** JWT-based auth with role management (Admin vs. Voter).
*   **Election Management:** Create, update, and manage elections and candidates.
*   **Tokenized Voting:** Unique, one-time-use tokens generated for every voter per election to prevent double voting.
*   **Tamper-Evident Logic:** Votes are linked via a hash chain (Blockchain concept), ensuring historical integrity.
*   **Automated Scheduling:** Background jobs (APScheduler) to automatically open/close elections.
*   **Real-time Results:** Instant calculation of election results.
*   **Automated Seeding:** The application automatically populates the database with rich mock data (50+ users, 10+ varied elections) on startup if the database is empty.

## 🛠 Tech Stack

*   **Language:** Python 3.10+
*   **Framework:** FastAPI
*   **Database:** SQLite (Easily swappable to PostgreSQL via Infrastructure layer)
*   **ORM:** SQLAlchemy
*   **Security:** Passlib (Bcrypt), PyJWT
*   **Testing:** Pytest

---

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have Python installed.

### 2. Setup Virtual Environment

```bash
cd Backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration
Ensure you have a `.env` file in the `Backend` root directory:

```ini
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your_super_secret_key_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## ▶️ Running the Application

From the `Backend` directory:

```bash
uvicorn main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

### API Documentation (Swagger UI)
Visit `http://127.0.0.1:8000/docs` to explore the interactive API documentation.

### Automated Seeding
On the first run, the system will detect an empty database and automatically seed it with:
*   **Admins:** `admin`, `moderator` (Password: `password123`)
*   **Voters:** `alice`, `bob`, ... and up to 50 generated users (Password: `password123`)
*   **Elections:** Diverse set of elections (Active, Pending, Completed).

---

##  Running Tests

The project includes a comprehensive test suite covering Auth, Elections, Candidates, and Voting flows.

From the `Backend` directory:

```bash
# Run all tests
cd tests
pytest -v
```

---

##  Project Tree

```text
Backend/
├── main.py                   # App Entry Point & Scheduler
├── requirements.txt
├── src/
│   ├── application/          # Services & Schemas (DTOs)
│   ├── core/                 # Config & Constants
│   ├── domain/               # Interfaces (Repositories)
│   ├── infrastructure/       # Database Models, Repositories, Security
│   └── presentation/         # API Routers & Dependencies
└── tests/                    # Integration & Unit Tests
```