![alt text](image.png)

# BUILD PHASE:

**Phase 1 - Project setup**
- Create project folder `sportflow_api`
- Create virtual environment `python3 -m venv venv`
- Activate virtual environment `source venv/bin/activate`
- Create folder structure: `routers/`, `models/`, `schemas/`, `services/`, `migrations/`
- Create root files: `main.py`, `database.py`, `.env`, `requirements.txt`
- Install dependencies `pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv pydantic passlib bcrypt python-jose`
- Database connection setup `database.py`
- Docker setup `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- SQLAlchemy models `models/models.py`
  - users: `id`, `email`, `hashed_password`, `first_name`, `last_name`, `role`, `created_at`, `updated_at`
  - products: `id`, `name`, `description`, `price`, `category`, `image_url`, `is_active` (True = available, False = soft delete), `created_at`, `updated_at`
  - inventory: `id`, `product_id`, `size`, `quantity`, `created_at`, `updated_at`
  - orders: `id`, `user_id`, `total_amount`, `status` (pending, confirmed, shipped, delivered, cancelled), `created_at`, `updated_at`
  - order_items: `id`, `order_id`, `product_id`, `quantity`, `price_at_purchase`
  - payments: `id`, `order_id`, `amount`, `status` (pending, completed, failed, refunded), `payment_method`, `created_at`, `updated_at`
- Alembic migrations

**Phase 2 - Auth**
- Register, login, JWT, RBAC
- User service and auth service

**Phase 3 - Products and inventory**
- Product endpoints
- Inventory endpoints with stock locking for race conditions

**Phase 4 - Cart**
- Redis introduction
- Cart service

**Phase 5 - Orders and payments**
- Order endpoints and service
- Payment endpoints and service

**Phase 6 - Polish and deployment**
- Tests
- Deployment to Render
- Portfolio update



# GENERAL DEV NOTES

## Python / SQLAlchemy

### SQLAlchemy imports rule
Import from SQLAlchemy anything that is a type or class: Column, String, Integer, DateTime, Boolean, ForeignKey, Numeric.
Do NOT import keyword arguments that go inside Column() with = signs: nullable, primary_key, default, onupdate, autoincrement. These are just parameters, not objects.

### datetime
utcnow() is deprecated in Python 3.12+. Use this instead:
from datetime import datetime, timezone
datetime.now(timezone.utc)

### default vs onupdate in SQLAlchemy
Use default=lambda: datetime.now(timezone.utc) for created_at, runs when record is created.
Use onupdate=lambda: datetime.now(timezone.utc) for updated_at, runs when record is updated.
Always use lambda so it runs fresh each time, not once when the file loads.

### Never use Float for money
Float has floating point precision issues, 0.1 + 0.2 gives 0.30000000000000004.
Use Numeric(precision=10, scale=2) for all monetary values.
precision = total digits, scale = digits after the decimal point.

### Quantity vs money types
Quantity is a whole number count, use Integer. Money needs decimals, use Numeric.

### Soft delete
Never delete records from the database. Add an is_active boolean column and set it to False instead. This preserves historical data and keeps old relationships intact.

### Nullable rule for timestamps
created_at should be nullable=False, it always has a value.
updated_at should be nullable=True, it has no value until the first update.

### Keyword argument order in Column()
The column type (String, Integer etc) goes first as a positional argument.
All keyword arguments after it (nullable, default, onupdate, primary_key) can be in any order.

### None comparison
Always use `is None` and `is not None`, never `== None`. PEP 8 standard,
None is a singleton so identity check is correct.

## Environment variables

### Professional pattern
Never hardcode a fallback connection string in code. Load .env with load_dotenv(),
read with os.getenv(), and raise a RuntimeError with a clear message if the
variable is missing. Fail loudly, not silently.

### .env vs migrations/env.py
.env is your environment variables file (secrets, connection strings).
migrations/env.py is Alembic's Python config file. Same name, completely different files.

### venv pip vs global pip
Upgrading pip globally on your machine does not affect pip inside your venv.
They are completely separate and independent.

### pip upgrade prompt
When pip says a new version is available, you can safely ignore it. Only upgrade
if a package install fails due to an outdated pip version.

## eCommerce concepts

### Why order_items table exists
Orders and products have a many to many relationship. One order can have many products, one product can appear in many orders. The order_items table sits between them. Each row is one product in one order. It also stores price_at_purchase so old orders are not affected by future price changes.

### Inventory vs products
Products table stores what a product IS: name, description, price, category.
Inventory table stores stock levels per variant: size, quantity. Separated because one product can have multiple sizes each with their own stock level.

### Inventory table naming
Table name is inventory, not inventories. It is one of the few exceptions to
the plural table naming convention.

### Race conditions and stock locking
Two users adding the same last item to cart is fine, cart does not reserve stock. Stock is only locked at checkout. The system locks the inventory record, checks quantity, and only one transaction succeeds. The other gets an item no longer available error.

### Cart storage
Cart lives in Redis, not PostgreSQL. Redis is in memory so it is much faster for temporary session data. The database is for permanent records only.

### Images in databases
Never store actual images in the database, too large and slow. Store the image
in something like AWS S3 and save only the URL string in the database.

## API / FastAPI

### CORS
Cross Origin Resource Sharing. Tells your API which domains are allowed to call it. Always configure it even without a frontend because it is production standard practice.

### add_middleware structure
app.add_middleware(MiddlewareClass, param=value, ...) takes the middleware class
first, then that middleware's settings. allow_credentials takes a boolean, not a list.

### models.py vs schemas.py
models.py contains SQLAlchemy classes that map to database tables.
schemas.py contains Pydantic classes that validate request and response data.
Never mix them into one file.

### Why services layer exists
Routers handle HTTP only. Services handle business logic. Keeps code clean and testable. One service per router is the standard pattern.

## Alembic

### Setup order
1. alembic init migrations (creates the migrations folder and config files)
2. Configure migrations/env.py (import Base and all models, set target_metadata = Base.metadata)
3. alembic revision --autogenerate -m "message" (generates the migration SQL)
4. alembic upgrade head (runs the migration, actually creates the tables)

### Why import all models in env.py
Importing the model classes loads them into memory so Base.metadata is populated.
Without it Alembic generates blank migrations.

## Docker

### Official Image vs Hardened Image
Use the Official Image for personal and portfolio projects. Hardened is for enterprises with strict compliance requirements. Docker markets it as recommended but most production backends use Official.

### Why WORKDIR /app
Sets the working directory inside the container. All subsequent commands run from there. Docker creates it automatically if it does not exist.

### CMD breakdown
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
uvicorn = the server, main:app = file and FastAPI instance name,
0.0.0.0 = accept external connections (not just inside the container), 8000 = port.

### .dockerignore essentials
Always ignore: venv/, __pycache__/, .env, any notes or documentation files.

## Project structure

### Why folders over single files
Even if a folder only has one file now, the folder structure leaves room to grow and keeps the root clean. Always think about how the project scales.

### Separating models into files
For small to medium projects one models.py is clean enough. For large codebases split into separate files per domain and use __init__.py to import them together.

## Classes vs instances

### Why SessionLocal() and FastAPI() have brackets
SessionLocal and FastAPI are classes (blueprints). Adding () creates an instance
(the actual object you use). Same as MyClass() in any Python code.

# INTERVIEW TALKING POINTS

## Architecture decisions

### Separation of concerns: customer vs admin routes
Customer facing routers (products, orders, cart, users, auth) are teal.
Admin only routers (inventory, payments) are coral. Knowing which endpoints 
should be restricted to admins shows you think about security and access control 
at the design stage, not as an afterthought.

### Why services layer exists
Routers handle HTTP only. Business logic lives in services. This makes code 
cleaner, testable, and easier to maintain. One service per router.

### Why order_items table exists
Orders and products have a many to many relationship. order_items sits between 
them. It also stores price_at_purchase so future price changes do not affect 
historical orders.

### Why inventory is a separate table from products
A product can have multiple variants like sizes. Each size has its own stock 
level. Storing stock inside products would make variant tracking messy.

### Soft delete on products
Used is_active boolean instead of deleting records. Preserves historical data 
and keeps old orders referencing the product intact.

### Cart in Redis not PostgreSQL
Cart is temporary session data. Redis is in memory and much faster than hitting 
the database for every cart update. Database is reserved for permanent records.

## Race conditions and stock locking
Two users can add the same last item to cart at the same time, cart does not 
reserve stock. Stock is only locked at checkout. The system locks the inventory 
record, checks quantity, and only one transaction succeeds. The other gets an 
item no longer available error. This is how real time eCommerce platforms handle 
concurrent purchases at scale.

## models.py vs schemas.py separation
Deliberately separated SQLAlchemy models from Pydantic schemas unlike some 
projects that mix them. models.py is database layer, schemas.py is API contract 
layer. Cleaner and easier to maintain.

## CORS configured even without a frontend
Added CORS middleware even though there is no frontend. Production standard 
practice. Shows understanding of how APIs work in a real world context.

## Splitting models into files
Kept all models in one models.py for this project size. Understand how to split 
into separate files per domain with __init__.py imports for larger codebases.