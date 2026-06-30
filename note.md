![alt text](image.png)

# BUILD PHASE:

## Phase 1 - Project setup ✅
- Create project folder `sportflow_api`
- Create virtual environment: `python3 -m venv venv`
- Activate virtual environment: `source venv/bin/activate`
- Create folder structure: `routers/`, `models/`, `schemas/`, `services/`, `migrations/`
- Create root files: `main.py`, `database.py`, `.env`, `requirements.txt`
- Install dependencies: `pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv pydantic passlib bcrypt python-jose email-validator`
- Add installed packages to `requirements.txt` (direct dependencies only)
- Database connection setup `database.py`:
  - Import DATABASE_URL from config.py
  - engine, SessionLocal, Base, get_db dependency
- main.py: FastAPI() instance, CORS middleware (allow all for now), root endpoint
- Docker setup:
  - `Dockerfile`: FROM python:3.14, WORKDIR /app, COPY requirements, RUN pip install, COPY . ., CMD uvicorn with host 0.0.0.0 port 8000
  - `docker-compose.yml`: db service (postgres:16, port 5432:5432, named volume), redis service (redis:7, port 6379:6379), api service (build ., port 8000:8000, depends_on db and redis)
  - Local DATABASE_URL and REDIS_URL use localhost. docker-compose uses service names (db, redis)
  - Secrets stay as ${SECRET_KEY} etc, pulled from .env
  - `.dockerignore`: venv/, __pycache__/, .env, notes
- SQLAlchemy models `models/models.py` (six tables):
  - users: id, email, hashed_password, first_name, last_name, role (customer, admin), created_at, updated_at
  - products: id, name, description, price, category, image_url, is_active (True = available, False = soft delete), created_at, updated_at
  - inventory: id, product_id (FK), size, quantity, created_at, updated_at
  - orders: id, user_id (FK), total_amount, status (pending, confirmed, shipped, delivered, cancelled), created_at, updated_at, items (relationship), payment (relationship, uselist=False)
  - order_items: id, order_id (FK), product_id (FK), quantity, price_at_purchase, order (relationship)
  - payments: id, order_id (FK), amount, status (pending, completed, failed, refunded), payment_method (card, paypal, apple_pay, google_pay, bank_transfer), created_at, updated_at, 
    order (relationship)
- Alembic migrations: alembic init → configure env.py → docker compose up -d db → autogenerate → upgrade head
  - `alembic init migrations`
  - In `migrations/env.py`: import os, import Base and ALL models, add `config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))`, set `target_metadata = Base.metadata`
  - Leave alembic.ini sqlalchemy.url as the default placeholder, never put real URLs in it
  - .env uses `localhost` host (tools on the Mac), docker-compose uses `db` host (containers)
  - Start database: `docker compose up -d db`
  - Generate migration: `alembic revision --autogenerate -m "create initial tables"`
  - Apply migration: `alembic upgrade head`
  - Verify tables in DBeaver (localhost:5432)
  - Run new migration after every model COLUMN change (relationships don't need migrations — they're Python-level, foreign keys already exist)
- Full stack test: `docker compose up -d --build`, check localhost:8000 and localhost:8000/docs
- Git setup (first time):
  - Create `.gitignore`: venv/, __pycache__/, .env, notes.md, diagram files
  - `git init`
  - `git branch -M main`
  - `git add .`
  - `git commit -m "message"`
  - Create empty repo on GitHub with a one line description
  - `git remote add origin https://github.com/Biralee11/sportflow-api.git`
  - `git push -u origin main`

## Phase 2 - Auth 🔄
- Generate real SECRET_KEY: `openssl rand -hex 32` → .env ✅
  - Never paste secrets anywhere (chat, Slack, tickets). If exposed, regenerate.
  - Production gets a DIFFERENT key, set in Render env vars at deployment
- Install email-validator: `pip install email-validator`, add to requirements.txt ✅
- Pin bcrypt version: pip install bcrypt==4.0.1, update requirements.txt
 - Newer bcrypt versions are incompatible with passlib, pin to 4.0.1
- config.py (root):
  - Single place for all env var loading and validation
  - load_dotenv() called once here, nowhere else
  - All variables read with os.getenv(), checked with RuntimeError if None
  - ACCESS_TOKEN_EXPIRE_MINUTES converted to int() after None check
  - All other files import from config, never from os.getenv directly
- schemas/schemas.py:
  - RegisterRequest: email (EmailStr), password (str = Field(min_length=8) + field_validator for uppercase and special char with specific error messages), 
    first_name (Field(min_length=1, max_length=50)), last_name (Field(min_length=1, max_length=50))
  - NO role field in RegisterRequest — role is hardcoded server-side as "customer" (never trust client input / privilege escalation prevention)
  - LoginRequest: email (str, deliberately NOT EmailStr), password (str, no validation rules)
  - UserResponse: id (int), email (str), first_name (str), last_name (str), role (str), created_at (datetime), updated_at (Optional[datetime] = None)
  - UserResponse used as response_model on register — strips hashed_password automatically
  - TokenResponse used as response_model on login. access_token (str), token_type (str)
- services/auth_service.py:
  - imports from config.py
  - CryptContext(schemes=["bcrypt"], deprecated="auto")
    deprecated="auto" future-proofs for algorithm migration later
  - hash_password(password: str) -> str
  - verify_password(plain_password: str, hashed_password: str) -> bool
  - create_access_token(data: dict) -> str — caller passes {"sub": user.email, "role": user.role}, function adds exp, iss, aud
  - verify_access_token(token: str) -> dict — raises HTTPException 401 if invalid or expired, never returns None
  - oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
  - get_current_user(token, db) -> UserModel — extracts email from payload["sub"], queries DB, raises 401 if not found
  - get_current_admin(current_user) -> UserModel — raises 403 "Insufficient permissions" if role != "admin"
- services/user_service.py:
  - Separate from auth_service.py which handles token/password operations
  - register(db, request): email uniqueness check, hash password, create UserModel with role="customer", add/commit/refresh, return user
  - login(db, request): query by email, verify password, raise 401 with generic message if either fails, return TokenResponse dict
  - Imports hash_password, verify_password, create_access_token from auth_service.py (services can call other services)
  - Future additions: get_user_by_id, update_user, change_password (for user router in Phase 6)
- routers/auth_router.py:
  - router = APIRouter(prefix="/auth", tags=["Auth"])
  - POST /register: calls user_service.register(db, request), response_model=UserResponse
  - POST /login: calls user_service.login(db, request), response_model=TokenResponse
  - Router is lean, no business logic, just HTTP wiring
- routers/init.py: empty file, makes routers a Python package
- main.py: register all routers with app.include_router(), e.g auth_router with app.include_router(auth_router.router)
- seed.py (root):
  - Creates the first admin user directly in the database (bootstrap problem)
  - Uses try/finally to ensure db.close() always runs
  - Run with: python seed.py (venv must be activated, db container must be running)
  - Never commit real admin credentials — use placeholder or remove before pushing
- Admin creation:
  - seed.py creates the first admin
  - Admin-only RBAC-protected endpoint creates/promotes further admins
  - Public /register can NEVER create an admin
- Test register: POST localhost:8000/auth/register with email, password, first_name, last_name
- Test login: POST localhost:8000/auth/login with email, password
- Verify JWT claims at jwt.io: sub, role, exp, iss, aud all present

## Phase 3 - Products and inventory
- Product endpoints (customer facing)
- Inventory endpoints with stock locking for race conditions (admin only)
- schemas/schemas.py additions:
  - ProductCreateRequest: name, description, price (Decimal), category, image_url (Optional)
  - ProductUpdateRequest: all fields Optional
  - ProductResponse: id, name, description, price, category, image_url, is_active, created_at, updated_at
  - InventoryCreateRequest: product_id, size, quantity
  - InventoryUpdateRequest: size and quantity both Optional
  - InventoryResponse: id, product_id, size, quantity, created_at, updated_at
- services/product_service.py:
  - Convention: db first in all service function signatures
  - get_all_products(db, page, limit): filter is_active==True, pagination with offset/limit
  - get_product_by_id(db, id): raises 404 if not found
  - create_product(db, request): creates ProductModel, add/commit/refresh
  - update_product(db, id, request): if-checks for each Optional field, commit/refresh
  - delete_product(db, id): soft delete, sets is_active=False, commit/refresh, returns product
- services/inventory_service.py:
  - get_all_inventory(db, page, limit): pagination, no is_active filter (admin sees all)
  - get_inventory_by_product(db, product_id): returns List, uses .all() not .first()
  - create_inventory(db, request): creates InventoryModel, add/commit/refresh
  - update_inventory(db, id, request): if-checks for size and quantity
  - delete_inventory(db, id): HARD delete (safe, order_items captures price_at_purchase), returns message dict
  - decrement_stock(db, id, quantity_requested): SELECT FOR UPDATE lock, 404 if not found, 409 if insufficient stock, decrement, commit (releases lock automatically), refresh, return inventory
- routers/products_router.py:
  - prefix="/products", tags=["Product"]
  - GET / : public, response_model=List[ProductResponse]
  - GET /{id}: public, response_model=ProductResponse
  - POST /: admin only, response_model=ProductResponse
  - PUT /{id}: admin only, response_model=ProductResponse
  - DELETE /{id}: admin only, response_model=ProductResponse (returns deactivated product)
  - Import service as module: from services import product_service, call product_service.function()
- routers/inventory_router.py:
  - prefix="/inventory", tags=["Inventory"]
  - All endpoints admin only
  - GET /: response_model=List[InventoryResponse]
  - GET /product/{product_id}: response_model=List[InventoryResponse]
  - POST /: response_model=InventoryResponse
  - PUT /{id}: response_model=InventoryResponse
  - DELETE /{id}: no response_model (returns message dict)
  - decrement_stock not wired to a router endpoint, called internally from order service in Phase 5
- main.py: registered auth_router, products_router, inventory_router

## Phase 4 - Cart
- Install redis: pip install redis, add to requirements.txt
- Add Redis to docker-compose.yml: redis service (redis:7, port 6379:6379), api depends_on redis
- Add REDIS_URL to .env (localhost) and docker-compose api environment (redis service name)
- Add REDIS_URL to config.py with RuntimeError guard
- schemas/schemas.py additions:
  - CartItemRequest: product_id Field(gt=0), size Field(min_length=1, max_length=20), quantity Field(gt=0) — gt=0 not ge=0, adding zero items makes no sense
  - CartItemResponse: product_id, size, quantity, price (Decimal)
- services/cart_service.py:
  - redis_client = redis.from_url(REDIS_URL) at module level
  - Cart key pattern: f"cart:{user_id}"
  - Item key pattern: f"{product_id}:{size}"
  - add_to_cart(db, user_id, request): fetch product (404 if not found or inactive), build item dict, json.dumps, redis_client.hset — no return needed
  - get_cart(user_id): hgetall, json.loads each value, return list of dicts
  - remove_from_cart(user_id, product_id, size): hdel — no return needed
  - No db session needed for get_cart and remove_from_cart (Redis only)
- routers/cart_router.py: prefix="/cart", all require get_current_user
  - POST /: add_to_cart, passes current_user.id (never trust client to send their own id)
  - GET /: get_cart, response_model=List[CartItemResponse]
  - DELETE /{product_id}/{size}: remove_from_cart
  - clear_cart (delete entire key)

## Phase 5 - Orders and payments
- Order endpoints and service
- Payment endpoints and service
- Checkout calls inventory_service.decrement_stock() with SELECT FOR UPDATE locking
- Checkout reads prices from database, never from client (never trust client input)
- services/order_service.py
- services/payment_service.py
- routers/orders_router.py
- routers/payments_router.py

## Phase 6 - Polish and deployment
- User router: GET /users/me, PUT /users/me (calls user_service functions)
- Tests
- Rate limiting with slowapi (protects register/login from enumeration and brute force)
- Deployment to Render (fresh SECRET_KEY in Render env vars, 2FA on accounts)
- Portfolio and LinkedIn update (post-deployment only)





# GENERAL DEV NOTES

## Python / SQLAlchemy

### SQLAlchemy imports rule
Import from SQLAlchemy anything that is a type or class: Column, String, Integer, DateTime, Boolean, ForeignKey, Numeric.
Do NOT import keyword arguments that go inside Column() with = signs: nullable, primary_key, default, onupdate, autoincrement. These are parameters, not objects.

### datetime
utcnow() is deprecated in Python 3.12+. Use:
from datetime import datetime, timezone
datetime.now(timezone.utc)

### Money types
SQLAlchemy: Numeric(precision=10, scale=2). Pydantic: Decimal (from decimal import Decimal).
Never Float for money.

### default vs onupdate in SQLAlchemy
default=lambda: datetime.now(timezone.utc) for created_at, runs on record creation.
onupdate=lambda: datetime.now(timezone.utc) for updated_at, runs on record update.
Always use lambda so it runs fresh each time, not once when the file loads.

### Never use Float for money
Float has precision issues, 0.1 + 0.2 gives 0.30000000000000004.
Use Numeric(precision=10, scale=2). precision = total digits, scale = decimal places.
precision and scale go INSIDE Numeric(): Column(Numeric(precision=10, scale=2))

### Soft delete vs hard delete
Soft delete: set is_active=False. Use for products, users, anything with historical relationships.
Hard delete: db.delete(). Safe for inventory size variants since order_items captures everything at purchase time.

### Quantity vs money types
Quantity is a count, use Integer. Money needs decimals, use Numeric.

### Nullable rule for timestamps
created_at: nullable=False, always has a value.
updated_at: nullable=True, empty until first update.

### Keyword argument order in Column()
Column type goes first (positional). All keyword arguments after it can be in any order.

### None comparison
Always `is None` / `is not None`, never `== None`. PEP 8, None is a singleton.

### Classes vs instances
SessionLocal and FastAPI are classes (blueprints). Adding () creates an instance.

### fail fast pattern in validators
checks that raise, then bare return value at the end. No else needed:
if not re.search(r"[A-Z]", value):
raise ValueError("must have uppercase")
if not re.search(r"[^a-zA-Z0-9]", value):
raise ValueError("must have special char")
return value

### Chaining SQLAlchemy query methods
.filter(), .offset(), .limit(), .with_for_update() must all be called BEFORE .all() or .first().
.all() and .first() execute the query and return results (list or object). You cannot chain methods onto results.

### SELECT FOR UPDATE (row locking)
db.query(Model).filter(...).with_for_update().first()
Locks the row for the duration of the transaction. Lock releases automatically on db.commit() or rollback.
Use for race condition prevention on concurrent stock decrements.

### is_active vs quantity (independent concerns)
is_active = False means "not for sale" (business decision).
quantity = 0 means "physically out of stock" (inventory state).
A product can be inactive with stock in the warehouse, or active with zero stock.
They are tracked independently by design.

### db.refresh(user) after commit
After db.commit(), the object in memory doesn't have database-generated values
like id or created_at yet. Call db.refresh(user) to fetch the updated record
back from the database before returning it.

## Pagination

### Pattern
GET endpoint accepts page: int = 1, limit: int = 20 as query parameters (defaults in router only).
Service function takes page and limit as required params (no defaults).
Query: .filter(...).offset((page - 1) * limit).limit(limit).all()
offset = how many records to skip. limit = how many to return.
FastAPI reads ?page= and ?limit= from URL automatically based on parameter names.

### When to add pagination
Any list endpoint that could grow large over time. Products, inventory, orders, etc.
Never return unbounded lists in production.

## Service layer conventions

### db first in service functions
def function_name(db: Session, id: int, request: Schema):
db always first, id/identifiers second, request data last.

### request first in router functions
def endpoint_name(request: Schema, id: int, db: Session = Depends(get_db), current_user = Depends(...)):
Body/path params first, dependencies (db, auth) last. Idiomatic FastAPI style.

### Services can call other services
user_service.py imports from auth_service.py. This is correct and professional.
The rule is routers don't contain business logic, not that services can't talk to each other.

### Import service as module in routers
from services import product_service
then call product_service.create_product(db, request)
Avoids name collision where router function name shadows imported service function name.

## Redis
In-memory data store. Extremely fast (microseconds). Not permanent by default.
Use for temporary/session data (cart). PostgreSQL for permanent records.

### Redis hash commands
hset(key, field, value) — add/update one field in a hash
hgetall(key) — get all fields and values in a hash (returns dict)
hdel(key, field) — delete one field from a hash

### Cart structure
Cart key: f"cart:{user_id}"
Item key: f"{product_id}:{size}"
Value: json.dumps({"product_id": ..., "size": ..., "quantity": ..., "price": ...})
Redis stores strings only — use json.dumps to store, json.loads to retrieve.
price stored as str(product.price) since Decimal is not JSON serializable.

### Redis connection
redis_client = redis.from_url(REDIS_URL) at module level. No session management needed.
REDIS_URL: localhost in .env (for Mac tools), redis service name in docker-compose.


Environment variables and config

config.py: one place, all vars, all RuntimeError guards, int() conversion after None check.
Secrets never committed. Local dev config (localhost URLs) safe to commit.
Twelve factor: same code runs everywhere, only env vars change.
Import execution: Python executes imported files fully before returning — RuntimeError fires at import time.

## Environment variables and config

### config.py pattern (professional standard)
Never scatter load_dotenv() and os.getenv() across multiple files.
Create config.py in the root, load and validate ALL env vars there,
import from it everywhere else. One place to change if config ever changes.

### Reading then converting env vars
Read first, check None, then convert:
value = os.getenv("KEY")
if value is None:
raise RuntimeError("KEY is not set")
value = int(value)
Never int(os.getenv("KEY")) in one line, int(None) throws TypeError with no useful message.

### Code vs config (twelve factor principle)
Code should never know which environment it runs in. Same database.py runs on Mac,
in Docker, on Render. Only the environment variable changes. Never hardcode
environment specific values in Python files.

### Secrets vs local dev config
Local dev config CAN be committed (postgres:postgres@localhost only works on your machine).
Secrets and production config NEVER get committed: SECRET_KEY, production database URLs,
live API keys, anything pointing at real infrastructure.

### Import execution order
When Python imports a file, it executes it top to bottom completely before
returning to the importing file. So RuntimeError in config.py fires at
import time, before any code in the importing file runs.

### .env vs migrations/env.py
.env = environment variables file. migrations/env.py = Alembic's Python config.
Same name, completely different files.

### venv pip vs global pip
Completely separate and independent. Upgrading one does not affect the other.

### pip upgrade prompt
Safe to ignore. Only upgrade if a package install fails due to outdated pip.

### Why ALGORITHM lives in .env even though it's not secret
Not about secrecy. About configurability — if you ever switch algorithms,
one .env change redeploys without touching code. Consistent with twelve factor:
all config in the environment, regardless of sensitivity.

## eCommerce concepts

### Why order_items table exists
Orders and products are many to many. order_items sits between them, one row per
product per order. Stores price_at_purchase so future price changes do not affect
historical orders.

### Inventory vs products
Products = what a product IS (name, description, price, category).
Inventory = stock levels per variant (size, quantity). Separate because one product
has multiple sizes, each with its own stock level.

### Inventory table naming
inventory, not inventories. Exception to the plural table naming convention.

### Race conditions and stock locking
Cart does not reserve stock, two users can add the same last item. Stock locks at
checkout via SELECT FOR UPDATE: lock the inventory record, check quantity, one transaction succeeds,
the other gets the updated (zero) quantity, and is rejected with 409 with a message like "item no longer available"

### Cart add vs checkout
Cart add does NOT reserve stock. Inventory lock happens at checkout via SELECT FOR UPDATE.

## True simultaneity does not exist
Even nanosecond-apart requests resolve sequentially at the hardware level:
network packets travel through physical cables with different latencies,
server hardware processes requests through a single bus,
CPU executes instructions sequentially per core,
memory controller serializes writes.
The database lock manager processes acquisition requests sequentially.
Physics determines the order before the lock manager ever needs to decide.
Client-side timing (device, network speed) does not determine who wins.
What matters is which request's data is processed by the DATABASE SERVER's hardware first.

### Product reactivation
Dedicated POST /{id}/reactivate endpoint mirrors soft delete. More explicit and auditable than adding is_active to update schema. Admin must intentionally call it.

### Cart storage
Cart lives in Redis (in memory, fast, temporary session data).
Database is for permanent records only.

### Images in databases
Never store images in the database. Store in S3 or similar, save only the URL string.

## API / FastAPI

### CORS
Cross Origin Resource Sharing, controls which domains may call your API.
Configure it even without a frontend, production standard.

## response_model
Filters output to declared fields only. Strips hashed_password automatically.
FastAPI serializes the return value through the Pydantic model to JSON.
Just return the object, no manual dict building needed.
List endpoints: response_model=List[SchemaName]. Import List from typing.

### add_middleware structure
app.add_middleware(MiddlewareClass, param=value, ...). Middleware class first,
then its settings. allow_credentials takes a boolean, not a list.

### models.py vs schemas.py
models.py = SQLAlchemy classes mapping to tables.
schemas.py = Pydantic classes validating requests/responses. Never mix.

### Why services layer exists
Routers handle HTTP only. Services hold business logic. One service per router.

### Response schemas / response_model (security)
Without a response_model, returning a SQLAlchemy object serializes EVERY column
including hashed_password. response_model = UserResponse filters output to only
declared fields, automatically, every time.
FastAPI intercepts the return value, feeds it through the Pydantic model, serializes to JSON.
You just return the object — no manual dictionary building needed.

### API layer vs frontend layer
The API decides what data LEAVES the server (response schemas).
The frontend decides what data gets DISPLAYED (UI code).
"The frontend hides sensitive data" is wrong thinking — sensitive data should
never leave the API in the first place.

### APIRouter prefix and tags
for example
router = APIRouter(prefix="/auth", tags=["Auth"])
prefix handles the URL path once — endpoints just define their own suffix (/register, /login).
tags group endpoints in Swagger docs. Change prefix in one place, all endpoints update.

### init.py in router folders
Required to make the folder a Python package so imports work.
Create an empty init.py in routers/, models/, schemas/, services/.

### Never trust client input
role, prices, is_active, user_id — always set or fetched server-side. current_user.id from JWT, not from request body.

## Alembic

### Setup order (new project)
1. alembic init migrations
2. Configure migrations/env.py: import os, Base, and all models;
   config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"));
   target_metadata = Base.metadata
3. Leave alembic.ini sqlalchemy.url as placeholder, never real URLs (it gets committed)
4. docker compose up -d db
5. alembic revision --autogenerate -m "message"
6. alembic upgrade head

### Why import all models in env.py
Loads them into memory so Base.metadata is populated. Without it Alembic
generates blank migrations.

### localhost vs db hostname
db only resolves inside the Docker network. Tools on your Mac (Alembic, DBeaver)
use localhost, which works because compose maps "5432:5432".

## Docker

### Official vs Hardened image
Official for personal/portfolio/most production. Hardened is for strict
enterprise compliance. Docker's "recommended" label is partly commercial.

### WORKDIR /app
Sets working directory in the container, all later commands run from there.
Created automatically if missing.

### CMD breakdown
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
uvicorn = server, main:app = file and instance name, 0.0.0.0 = accept external
connections, 8000 = port.

### .dockerignore essentials
venv/, __pycache__/, .env, notes and documentation files.

### Port conflicts between projects
Two projects cannot map the same host port simultaneously. If 5432 is busy,
the other project's db container is probably running. Down it first or map
a different host port like "5433:5432".

### Reading docker ps PORTS column
"0.0.0.0:5432->5432/tcp" = published to your machine (the arrow is the mapping).
"5432/tcp" alone = only exposed inside Docker, unreachable from outside.
Weird container state: docker compose down then up recreates cleanly.

## Git

### First time setup
1. Create .gitignore BEFORE first commit (venv/, __pycache__/, .env, notes)
2. git init
3. git branch -M main
4. git add . && git commit -m "message"
5. Create empty GitHub repo with one line description (never leave it empty)
6. git remote add origin <url>
7. git push -u origin main (-u links local main to remote main)

### Day to day flow
git add . → git commit -m "message" → git push

### Check nothing sensitive is tracked
git ls-files | grep -E "^venv/|^\.env$"
Escape the dot: .env unescaped matches any character + "env" (false positives
like migrations/env.py).

## Regex

### Literal dot
A bare . matches any character. Use \. for a literal dot.

## Auth concepts

### RBAC (Role Based Access Control)
Every user has a role (customer, admin) stored in the users table. Endpoints
check the role before allowing access. Implemented via a dependency that reads
the role from the JWT. get_current_user returns user, get_current_admin checks role.
Protected endpoints use Depends(get_current_user) or Depends(get_current_admin).
current_admin parameter doesn't need to be used in the function body, its presence triggers the check.

### 401 vs 403
401 identity unknown = we don't know who you are (missing/invalid token).
403 identity known, insufficient permission = we know who you are, but you're not allowed to do this.
If Token valid but user deleted = 401 (identity unconfirmable).

### Hashing vs encryption
Encryption is two-way by design, a key exists to reverse it. Hashing is one-way
by design, no reverse function exists at all. Passwords are ALWAYS hashed, never
encrypted. Login works by hashing the attempt and comparing hashes, nothing is
ever unhashed. Even the developer cannot read user passwords.

### bcrypt vs passlib
bcrypt is the actual algorithm library. passlib (CryptContext) is a wrapper
supporting multiple algorithms and handling verification/migration logic.
Both do the same underlying math today, but passlib future-proofs the system.

### Salting and why hashes look different every time
bcrypt mixes in a random "salt" before hashing, so the SAME password produces
a DIFFERENT hash every time. The salt is embedded as a prefix in the hash string
itself (2b$12
... = algorithm version, cost factor, salt, then hash).
verify() extracts the salt FROM the stored hash, re-hashes the attempt with that
same salt, and compares. Same salt + same password = same result every time.

### bcrypt + passlib version pin

bcrypt==4.0.1. Pin in requirements.txt AND install locally in venv.

### schemes list and deprecated="auto"
schemes=["argon2", "bcrypt"]: first scheme used for all NEW hashes, rest kept
to verify OLD hashes. deprecated="auto" flags old-scheme logins so the system
can silently re-hash with the new algorithm on next successful login.
Enables algorithm migration with zero forced password resets.

### Password hashing library comparison
pwdlib: direct passlib successor, actively maintained, same multi-scheme
migration concept, no version conflicts. Recommended for new projects.
Install: pip install pwdlib[argon2]

argon2-cffi: standalone argon2 library, well maintained, but no multi-scheme
abstraction. You own migration logic yourself.

bcrypt directly: simplest, no wrapper, always compatible with itself,
but you own everything including migration.

Recommended stack for new projects: pwdlib + argon2
SportFlowAPI uses passlib + bcrypt (already built, pinned to 4.0.1)

### bcrypt version compatibility
bcrypt versions above 4.0.1 are incompatible with passlib and cause a ValueError
on hashing. Always pin: bcrypt==4.0.1 in requirements.txt.
Apply in both local venv (pip install bcrypt==4.0.1) and Docker (requirements.txt).

### Generic login errors (user enumeration)
Wrong email and wrong password return the SAME message ("Invalid email or password").
Different messages let attackers confirm which emails are registered by firing
bulk login attempts. Same principle applies to get_current_user: "Could not
validate credentials" is deliberately vague.

### Never trust client input / privilege escalation
Any field the client controls is an attack surface. Security-critical values
(role, prices, balances, is_active) are NEVER accepted from request bodies,
always set server-side. If role were in RegisterRequest, any user could send
"role": "admin" and own every admin endpoint.

### Admin creation pattern
Public registration hardcodes role="customer" server-side. First admin comes
from a seed script (bootstrap problem). Further admins only via admin-only
RBAC-protected endpoint.

### Seed scripts
Used to insert the first admin (bootstrap problem — no admin exists yet to create one).
Uses SessionLocal() directly (no dependency injection in scripts).
Always wrap in try/finally to ensure db.close() runs.
Run from terminal: python seed.py (venv activated, db container running).

### Secret handling
Secrets never leave their secure home (.env locally, platform env vars in
production). Never paste into chat, Slack, tickets, email. A secret that has
been seen anywhere else is burned, regenerate it. Each environment gets its own key.

### Defence in depth
Never claim a system can't be hacked. Reduce likelihood, limit damage:
2FA on all production accounts, short token expiry, key rotation, rate limiting,
CAPTCHA, secrets managers (Vault, AWS Secrets Manager) at larger scale.

### OAuth2PasswordBearer
Tells FastAPI where the login endpoint is (tokenUrl) so it knows how to extract
Bearer tokens from Authorization headers automatically.

### get_current_user vs get_current_admin
get_current_user: extracts token, verifies it, queries DB, returns user. Raises 401.
get_current_admin: calls get_current_user via Depends, then checks role. Raises 403.
Protected endpoints use one or the other as a Depends parameter.

### JWT payload is readable but not writable
JWT payloads are base64 encoded, not encrypted. Anyone can decode and read them.
The signature prevents modification: change any payload field and the signature
no longer matches. SECRET_KEY is the only thing preventing forgery.
Verify at jwt.io — paste any token to see the claims.

### Secret handling
Secrets never leave their secure home (.env locally, platform env vars in
production). Never paste into chat, Slack, tickets, email. A secret that has
been seen anywhere else is burned, regenerate it. Each environment gets its
own key so one leak doesn't compromise the others.

## Pydantic

### EmailStr
Never hand-roll email regex. Use EmailStr as the field type, requires
`pip install email-validator`. Validation and clear errors come free.

### Field for simple constraints
Field(min_length=8), Field(min_length=1, max_length=50) handle length rules
without writing validators. Custom validators only for genuinely custom rules.

### Validating names
Length limits only. No regex. Real names contain hyphens, apostrophes, spaces,
accents, every alphabet. See "Falsehoods Programmers Believe About Names".

### Password policy
Minimum 8 characters, NO low maximum cap (longer = exponentially stronger, and
hashing makes length free). Never force a specific starting character. Every
rejection message says exactly which rule failed.

### requirements.txt convention
List only direct dependencies. Dependencies of dependencies (like dnspython
under email-validator) are resolved by pip automatically.

### Login schema has no password validation
The hash comparison is the only judge. Validating complexity on login is
pointless and dangerous: if the policy tightens later, users with older
passwords get locked out. Plain str for email keeps all login failures
returning the same generic error.

### Response schemas need no validators
Response schemas (UserResponse etc) just declare shape and types for
serialization. No field_validator, no Field constraints needed — Pydantic's
job here is type checking on the way OUT, not rule enforcement on the way in.

### datetime (Pydantic/Python) vs DateTime (SQLAlchemy)
models.py uses DateTime (SQLAlchemy column type), from sqlalchemy.
schemas.py uses datetime (Python's own class), from datetime import datetime.
Same concept, different files, different imports.

### Optional[X] vs Optional[X] = None
Optional[X] alone = field can hold X or None, but must be explicitly present
in the input (omitting it entirely raises "field required").
Optional[X] = None = field can hold X or None, AND can be omitted entirely,
defaulting to None if absent.
For nullable=True columns (like updated_at), always use Optional[X] = None.





# DOCUMENT 3: INTERVIEW TALKING POINTS

## Architecture decisions

### Customer facing vs admin only routes
Products, orders, cart, users, auth are customer facing (teal in diagram).
Inventory and payments are admin only (coral). Designing access control at the
architecture stage shows security thinking from day one.

### Services layer
Routers handle HTTP only, business logic lives in services, one service per
router. Cleaner, testable, maintainable.

### Auth refactor
Refactored auth router to move register/login logic into user_service.py, keeping the router responsible only for HTTP concerns. Shows awareness of clean architecture, not just "does it work".

### Why order_items exists
Many to many between orders and products. Captures price_at_purchase so
historical orders are immune to future price changes.

### Inventory as a separate table
Products can have variants (sizes), each with independent stock. Stock inside
the products table cannot model that cleanly.

### Soft delete vs hard delete
Products = soft delete (is_active=False). Preserves history. Inventory size variants = hard delete (safe, no orphan risk since order_items captures purchase data).

### is_active vs quantity
is_active = business decision (are we selling this?). quantity = physical stock count. Independent by design. A product can be inactive with warehouse stock, or active with zero stock in one size.

### Cart in Redis not PostgreSQL
Temporary, high frequency session data belongs in memory. Database is for
permanent records. Much faster cart operations.

### models.py vs schemas.py separation
Database layer and API contract layer deliberately separated. Cleaner and
easier to maintain than mixing them.

### CORS configured without a frontend
Production standard practice. Shows understanding of how APIs serve real
frontends in the wild.

### One models.py vs split files
Deliberate choice for this project size. Understand how to split per domain
with __init__.py imports for larger codebases. Structure should match scale.

### Pagination on list endpoints
Added to all list endpoints. Prevents unbounded responses. Shows awareness of real-world scale, not just "does it work on my laptop". Uses page/limit query params, offset calculation server-side.

---

## Data integrity

### Numeric/Decimal over Float for money
Float precision errors are unacceptable for financial data. Numeric(10,2) in SQLAlchemy, Decimal in Pydantic. Knowing this matters in fintech and eCommerce.

### response_model as security
Strips hashed_password automatically on every response even if endpoint returns full ORM object.

---

## Configuration and security

### Code vs config separation (twelve factor)
Code never knows its environment. Same database.py runs locally, in Docker, on
Render. Only environment variables change. No hardcoded fallbacks, fail loudly
if config is missing.

### config.py as single source of truth
All env vars loaded, validated, converted in one file. Every other file imports
from config. Fail-fast RuntimeError on startup if anything is missing.

### Secrets vs local dev config
Local dev credentials (postgres:postgres@localhost) are safe to commit, they
only work on the developer's machine. Secrets live only in .env locally and
platform env vars in production. Never in the repo.

### Alembic reads config from environment
No credentials in alembic.ini (committed to git). env.py overrides
sqlalchemy.url from the environment at runtime.

---

## Race conditions and concurrency

### SELECT FOR UPDATE
Row-level lock at checkout. One transaction proceeds, concurrent transactions pause, get updated quantity, rejected with 409 Insufficient stock. Cart add never reserves stock.

### True simultaneity doesn't exist
Network packets travel through physical cables with real latency differences. Server hardware and CPU process instructions sequentially. Memory controller serializes writes. Lock manager processes acquisition requests sequentially. Physics determines order before the lock manager decides anything. Client-side timing (device/network) is irrelevant, server-side hardware processing order is what matters.

### Interview-ready line
"Row-level locking guarantees serializability of conflicting transactions even under concurrent load, because the lock manager processes acquisition requests sequentially. At a physical level, true simultaneity doesn't exist — hardware and network physics impose a sequential order before the lock manager needs to make any decision."

## Auth and security

### config.py as single source of truth
All env vars loaded, validated, fail-fast RuntimeError on startup.

### Twelve factor / code vs config
Same code runs everywhere. Only env vars change. No hardcoded fallbacks.

### Secrets vs local dev config
postgres:postgres@localhost is safe to commit (only works on your machine). SECRET_KEY, production URLs, API keys never committed.

### Hashing vs encryption (classic interview question)
Encryption is reversible by design (key exists). Hashing is one-way by design
(no reverse exists). Login compares hashes, never unhashes. Even the developer
cannot read user passwords.

### Salting explained
Same password produces different hashes each time because bcrypt embeds a random
salt. verify() extracts the salt from the stored hash, re-hashes the attempt
with it, and compares. Shows you understand the mechanism, not just the API call.

### JWT payload is readable but not writable
JWT payloads are base64 encoded, not encrypted. Anyone can decode and read them.
But the signature prevents modification: change any payload field and the
signature no longer matches. SECRET_KEY is the only thing preventing forgery.
Classic interview question: "Are you comfortable with JWT payloads being readable?"
Answer: yes, because they contain no secrets and the signature makes them tamper-proof.

### User enumeration prevention
Login returns the same generic error for wrong email and wrong password.
Register leaks similar info, mitigated with rate limiting (Phase 6), CAPTCHA,
or verify-by-email patterns. Applies throughout: "Could not validate credentials"
on get_current_user is also deliberately vague.

### Privilege escalation / never trust client input
role is not a field in RegisterRequest. If it were, any user could send
"role": "admin" and own every admin endpoint. Same principle protects
prices at checkout in Phase 5. Never trust client input for security-critical fields.

### Admin bootstrap
First admin via seed script (no admin exists yet to create one). Further admins
via admin-only RBAC-protected endpoint. Public registration can never produce an admin.

### Token valid but user deleted
If an account is deleted but the token hasn't expired, the token passes
cryptographic verification but the DB query returns None. Raises 401, not 403,
because the identity cannot be confirmed. Shows you think about edge cases.

### deprecated="auto" for algorithm migration
Existing hashes keep working, new registrations use the new algorithm,
existing users silently migrate on next successful login. Zero forced password
resets. Senior-level thinking about long-term maintenance.

### Defence in depth mindset
Never say "this can't be hacked". Say "here's how I reduce the chance and limit
the damage": 2FA, short token expiry (30 min), key rotation, separate keys per
environment, rate limiting, secrets managers at scale.

### 401 vs 403
401 = identity unknown (bad/missing token). 403 = identity known, permission
insufficient. Using them correctly signals API literacy.

### Password policy reasoning
Min 8 chars with complexity rules, no low max cap. Long passphrases are
exponentially stronger and hashing makes storage length-independent. Rejecting
a 40-char password is an anti-pattern.

### response_model as a security feature
Declaring response_model = UserResponse actively strips fields like
hashed_password from every response, even if the endpoint returns the full ORM
object. Defence in depth applied to outgoing data.

### API layer vs frontend layer
The API decides what data leaves the server. The frontend decides what gets
displayed. Saying "the frontend hides sensitive data" is a red flag — it implies
the frontend is a security boundary. It isn't.

### get_current_user dependency chain
FastAPI's Depends chains automatically: get_current_admin calls
Depends(get_current_user), which calls Depends(oauth2_scheme) and Depends(get_db).
The whole chain resolves before the endpoint runs. Shows understanding of
FastAPI's dependency injection.

### Race conditions and stock locking
Cart add does not reserve stock. At checkout the system locks the inventory row,
checks quantity, exactly one concurrent transaction succeeds. Real time eCommerce
handling concurrent purchases at scale. (Phase 3.)

### Rate limiting (Phase 6)
slowapi will be added to protect register and login endpoints from enumeration
and brute force attacks. Shows awareness of production hardening beyond just
making the happy path work.

### Password hashing library awareness
Know the landscape beyond just passlib. pwdlib is the modern successor to
passlib, actively maintained, same multi-scheme migration concept but without
the bcrypt version conflicts. argon2 is the stronger algorithm (won NIST's
password hashing competition in 2015). For new projects: pwdlib + argon2.
Shows you evolve your stack deliberately, not just copy what you last used.

### bcrypt version pinning
Newer bcrypt versions break passlib compatibility. Pinned to bcrypt==4.0.1.
Shows awareness of dependency management in production systems, not just
installing latest and hoping for the best.

---
## ADDENDUM: Race conditions deep dive

### SELECT FOR UPDATE mechanism
Lock acquired on row. Concurrent transaction waits. First transaction checks quantity, decrements, commits. Lock releases. Second transaction resumes, sees updated (zero) quantity, raises 409.

### Why true simultaneity doesn't exist
1. Network: physical cable/router latency differences mean nanosecond arrival gaps
2. Hardware: single bus, sequential CPU instruction execution, serialized memory writes
3. Database: lock manager itself processes acquisition requests sequentially
  By the time SELECT FOR UPDATE executes, physics has already imposed an order.

### Client vs server timing
Customer's device and network speed don't decide who wins. The DATABASE SERVER's hardware processing order determines it. Don't conflate these in an interview.