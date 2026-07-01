# SportFlowAPI

A production-ready sports eCommerce backend API built with FastAPI, PostgreSQL, Redis and Docker. It powers the backend of an online sports store, handling everything from user authentication and product catalogues to real-time inventory management, cart sessions, and atomic checkout with payments.

**Live API:** https://sportflow-api.onrender.com
**Interactive docs (Swagger):** https://sportflow-api.onrender.com/docs

---

## Overview

SportFlowAPI is a REST API that a frontend (web or mobile) would call to run an online sports store. It is a backend-only project focused on the architecture, data integrity, and security concerns that matter in a real eCommerce platform operating at scale.

The project was built in deliberate phases, from project setup and authentication through to orders, payments, testing, and deployment, with every decision made to production standard rather than tutorial standard.

---

## Tech stack

- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL (via SQLAlchemy ORM, migrations with Alembic)
- **Cache / sessions:** Redis
- **Authentication:** JWT (python-jose), password hashing with passlib and bcrypt
- **Containerisation:** Docker and docker-compose
- **Testing:** pytest with FastAPI TestClient
- **Rate limiting:** slowapi
- **Production hosting:** Render (app), Neon (PostgreSQL), Upstash (Redis)

---

## Key features

- **JWT authentication with Role Based Access Control (RBAC).** Separate customer and admin roles, with admin-only endpoints protected by dependency-based role checks.
- **Product management** with a soft-delete pattern (`is_active`) so historical data and past orders are never broken by removing a product, plus a dedicated reactivation endpoint.
- **Inventory management** with per-size stock tracking, modelled as a separate table so a single product can have multiple size variants each with independent stock.
- **Race-condition-safe stock decrementing** at checkout using PostgreSQL row-level locking (`SELECT ... FOR UPDATE`), so two customers cannot both buy the last item in stock.
- **Redis-backed cart** for fast, temporary session data, kept separate from the permanent PostgreSQL records.
- **Atomic checkout transaction.** Placing an order creates the order, its line items, and the payment record, decrements stock, and clears the cart, all in a single database transaction that fully rolls back on any failure.
- **IDOR protection** on user-owned resources, so customers can only ever access their own orders.
- **Rate limiting** on authentication endpoints to protect against brute force and user enumeration attacks.
- **Pagination** on all list endpoints to handle large catalogues gracefully.
- **Automated test suite** covering authentication, RBAC, stock limits, and the full checkout flow, running against an isolated test database.

---

## Architecture

The project follows a clean, layered structure that keeps concerns separated:

```
sportflow_api/
├── routers/          # HTTP layer only (request handling, no business logic)
├── services/         # Business logic (one service per domain)
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic request/response validation
├── migrations/       # Alembic database migrations
├── tests/            # pytest test suite
├── config.py         # Single source of truth for environment config
├── database.py       # Database engine and session setup
├── seed.py           # Creates the first admin user
├── Dockerfile
└── docker-compose.yml
```

**Layering principle:** routers handle HTTP concerns only and stay lean, delegating all business logic to the service layer. Services can call one another (for example, the order service calls the payment service within the same transaction), while models and schemas keep the database layer and the API contract cleanly separated.

---

## Data model

| Table | Purpose |
|-------|---------|
| `users` | Accounts with role (customer or admin) and hashed passwords |
| `products` | Product catalogue with soft-delete support |
| `inventory` | Per-size stock levels, linked to products |
| `orders` | Order records with status and total |
| `order_items` | Line items per order, capturing price at time of purchase |
| `payments` | Payment records linked one-to-one with orders |

Monetary values use `Numeric` rather than `Float` to avoid floating-point precision errors. Orders capture `price_at_purchase` on each line item so historical orders are never affected by later price changes.

---

## Getting started (local development)

### Prerequisites

- Docker and docker-compose
- Python 3.14 (for running tests and migrations locally)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Biralee11/sportflow-api.git
   cd sportflow-api
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sportflow_db
   TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sportflow_test_db
   REDIS_URL=redis://localhost:6379
   SECRET_KEY=your-generated-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_ISSUER=sportflow-api
   JWT_AUDIENCE=sportflow-client
   ADMIN_PASSWORD=your-admin-password
   ```

   Generate a secure secret key with:
   ```bash
   openssl rand -hex 32
   ```

3. Start the full stack (app, PostgreSQL, Redis):
   ```bash
   docker compose up -d --build
   ```

4. Run the database migrations:
   ```bash
   docker compose up -d db
   alembic upgrade head
   ```

5. Create the first admin user:
   ```bash
   python seed.py
   ```

6. Visit the API:
   - App: http://localhost:8000
   - Docs: http://localhost:8000/docs

---

## Running the tests

The test suite runs against a separate, isolated test database so it never touches development data.

```bash
pytest
```

Tests cover registration, login, invalid credentials, RBAC enforcement, insufficient-stock rejection, and a full successful checkout that verifies stock is correctly decremented.

---

## API endpoints

| Area | Method & Path | Access | Description |
|------|---------------|--------|-------------|
| Auth | `POST /auth/register` | Public | Register a new customer |
| Auth | `POST /auth/login` | Public | Log in and receive a JWT |
| Products | `GET /products` | Public | Browse active products (paginated) |
| Products | `GET /products/{id}` | Public | View a single product |
| Products | `POST /products` | Admin | Create a product |
| Products | `PUT /products/{id}` | Admin | Update a product |
| Products | `DELETE /products/{id}` | Admin | Soft-delete a product |
| Products | `POST /products/{id}/reactivate` | Admin | Reactivate a product |
| Inventory | `GET /inventory` | Admin | View all inventory (paginated) |
| Inventory | `GET /inventory/product/{product_id}` | Admin | View stock for a product |
| Inventory | `POST /inventory` | Admin | Add stock for a size |
| Inventory | `PUT /inventory/{id}` | Admin | Update stock |
| Inventory | `DELETE /inventory/{id}` | Admin | Remove a size variant |
| Cart | `POST /cart` | Customer | Add an item to cart |
| Cart | `GET /cart` | Customer | View cart |
| Cart | `DELETE /cart/{product_id}/{size}` | Customer | Remove one item |
| Cart | `DELETE /cart` | Customer | Clear the whole cart |
| Orders | `POST /orders` | Customer | Place an order (checkout) |
| Orders | `GET /orders` | Customer | View own orders (paginated) |
| Orders | `GET /orders/{id}` | Customer | View a specific own order |
| Orders | `PUT /orders/{id}/status` | Admin | Update order status |
| Users | `GET /users/me` | Customer | View own profile |
| Users | `PUT /users/me` | Customer | Update own profile |
| Users | `PUT /users/me/password` | Customer | Change own password |

---

## Notable design decisions

- **Soft delete over hard delete** for products and financial records, preserving audit trails and historical integrity.
- **Prices are always re-fetched from the database at checkout**, never trusted from the cart or the client, protecting against tampering and stale pricing.
- **Security-critical fields are never accepted from the client.** Roles, prices, and user IDs are always set or derived server-side.
- **Payment status is intentionally not updated via a manual endpoint**, reflecting that real systems handle this through payment-provider webhooks.
- **Config is fully environment-driven** following twelve-factor principles, so the same code runs unchanged locally, in Docker, and in production.

---

## Author

Eyebira Odugba
Backend Software Engineer

- Portfolio: https://biraodugba.com
- GitHub: https://github.com/Biralee11
