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
  - `docker-compose.yml`: db service (postgres:16, port 5432:5432, named volume), api service (build ., port 8000:8000, depends_on db)
  - Local DATABASE_URL written explicitly in compose with `db` host (local dev config, safe to commit)
  - Secrets stay as ${SECRET_KEY} etc, pulled from .env
  - `.dockerignore`: venv/, __pycache__/, .env, notes
- SQLAlchemy models `models/models.py` (six tables):
  - users: id, email, hashed_password, first_name, last_name, role (customer, admin), created_at, updated_at
  - products: id, name, description, price, category, image_url, is_active (True = available, False = soft delete), created_at, updated_at
  - inventory: id, product_id (FK), size, quantity, created_at, updated_at
  - orders: id, user_id (FK), total_amount, status (pending, confirmed, shipped, delivered, cancelled), created_at, updated_at
  - order_items: id, order_id (FK), product_id (FK), quantity, price_at_purchase
  - payments: id, order_id (FK), amount, status (pending, completed, failed, refunded), payment_method (card, paypal, apple_pay, google_pay, bank_transfer), created_at, updated_at
- Alembic migrations:
  - `alembic init migrations`
  - In `migrations/env.py`: import os, import Base and ALL models, add `config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))`, set `target_metadata = Base.metadata`
  - Leave alembic.ini sqlalchemy.url as the default placeholder, never put real URLs in it
  - .env uses `localhost` host (tools on the Mac), docker-compose uses `db` host (containers)
  - Start database: `docker compose up -d db`
  - Generate migration: `alembic revision --autogenerate -m "create initial tables"`
  - Apply migration: `alembic upgrade head`
  - Verify tables in DBeaver (localhost:5432)
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
- schemas/schemas.py:
  - RegisterRequest: email (EmailStr), password (Field min_length=8 + validator
    for uppercase and special char, specific error messages), first_name,
    last_name (Field min_length=1, max_length=50)
  - NO role field — role is hardcoded server-side as "customer" (never trust client input)
  - LoginRequest: email (str, deliberately NOT EmailStr — keeps malformed
    emails flowing through the same generic error path), password (str,
    no validation rules — hash comparison is the only judge)
  - UserResponse: id (int), email (str), first_name (str), last_name (str),
    role (str), created_at (datetime), updated_at (Optional[datetime] = None
    — matches nullable=True on the model)
  - UserResponse used as response_model on register, login, get-profile —
    filters out hashed_password automatically
- config.py (root):
  - Single place for all env var loading and validation
  - load_dotenv() called once here, nowhere else
  - All variables read with os.getenv(), checked with RuntimeError if None
  - ACCESS_TOKEN_EXPIRE_MINUTES converted to int() after None check
  - All other files import from config, never from os.getenv directly
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
  - User specific business logic: fetch user by id, update profile, change password
  - Separate from auth_service.py which handles token/password operations
- routers/auth_router.py:
  - POST /auth/register: validate RegisterRequest → check email not taken → 
    hash password → create UserModel with role="customer" → add, commit → 
    return UserResponse
  - POST /auth/login: validate LoginRequest → query user by email → verify 
    password → create JWT with sub, role → return token
- Auth flow to implement:
  - Register: validate schema → check email not already registered → hash password → create UserModel with role="customer" → add, commit → return UserResponse
  - Login: generic "invalid login details" for both wrong email and wrong password (user enumeration prevention) → 
    verify password by hashing attempt and comparing → issue JWT with sub, role, exp, iss, aud
- Admin creation:
  - seed script creates the first admin (bootstrap problem)
  - admin-only RBAC-protected endpoint creates/promotes further admins
- RBAC dependency: reads role from JWT, 401 = unknown identity, 403 = known
  but insufficient role

## Phase 3 - Products and inventory
- Product endpoints (customer facing)
- Inventory endpoints with stock locking for race conditions (admin only)

## Phase 4 - Cart
- Redis introduction and setup
- Cart service (stores in Redis, not PostgreSQL)

## Phase 5 - Orders and payments
- Order endpoints and service
- Payment endpoints and service
- Checkout reads prices from database, never from client (never trust client input)

## Phase 6 - Polish and deployment
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

### default vs onupdate in SQLAlchemy
default=lambda: datetime.now(timezone.utc) for created_at, runs on record creation.
onupdate=lambda: datetime.now(timezone.utc) for updated_at, runs on record update.
Always use lambda so it runs fresh each time, not once when the file loads.

### Never use Float for money
Float has precision issues, 0.1 + 0.2 gives 0.30000000000000004.
Use Numeric(precision=10, scale=2). precision = total digits, scale = decimal places.
precision and scale go INSIDE Numeric(): Column(Numeric(precision=10, scale=2))

### Quantity vs money types
Quantity is a count, use Integer. Money needs decimals, use Numeric.

### Soft delete
Never delete records. Use an is_active boolean set to False. Preserves historical
data and keeps old relationships intact.

### Nullable rule for timestamps
created_at: nullable=False, always has a value.
updated_at: nullable=True, empty until first update.

### Keyword argument order in Column()
Column type goes first (positional). All keyword arguments after it can be in any order.

### None comparison
Always `is None` / `is not None`, never `== None`. PEP 8, None is a singleton.

### Classes vs instances
SessionLocal and FastAPI are classes (blueprints). Adding () creates an instance.

## Environment variables and config

### Professional pattern
Never hardcode a fallback connection string in code. load_dotenv(), os.getenv(),
raise RuntimeError with a clear message if missing. Fail loudly, not silently.

### Code vs config (twelve factor principle)
Code should never know which environment it runs in. Same database.py runs on Mac,
in Docker, on Render. Only the environment variable changes. Never hardcode
environment specific values in Python files.

### Secrets vs local dev config
Local dev config CAN be committed (postgres:postgres@localhost only works on your machine).
Secrets and production config NEVER get committed: SECRET_KEY, production database URLs,
live API keys, anything pointing at real infrastructure.

### .env vs migrations/env.py
.env = environment variables file. migrations/env.py = Alembic's Python config.
Same name, completely different files.

### venv pip vs global pip
Completely separate and independent. Upgrading one does not affect the other.

### pip upgrade prompt
Safe to ignore. Only upgrade if a package install fails due to outdated pip.

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
checkout only: lock the inventory record, check quantity, one transaction succeeds,
the other gets "item no longer available".

### Cart storage
Cart lives in Redis (in memory, fast, temporary session data).
Database is for permanent records only.

### Images in databases
Never store images in the database. Store in S3 or similar, save only the URL string.

## API / FastAPI

### CORS
Cross Origin Resource Sharing, controls which domains may call your API.
Configure it even without a frontend, production standard.

### add_middleware structure
app.add_middleware(MiddlewareClass, param=value, ...). Middleware class first,
then its settings. allow_credentials takes a boolean, not a list.

### models.py vs schemas.py
models.py = SQLAlchemy classes mapping to tables.
schemas.py = Pydantic classes validating requests/responses. Never mix.

### Why services layer exists
Routers handle HTTP only. Services hold business logic. One service per router.

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
the role from the JWT.

### 401 vs 403
401 Unauthorised = we don't know who you are (missing/invalid token).
403 Forbidden = we know who you are, but you're not allowed to do this.

### Hashing vs encryption
Encryption is two-way by design, a key exists to reverse it. Hashing is one-way
by design, no reverse function exists at all. Passwords are ALWAYS hashed, never
encrypted. Login works by hashing the attempt and comparing hashes, nothing is
ever unhashed.

### Generic login errors (user enumeration)
Wrong email and wrong password must return the SAME message ("invalid login
details"). Different messages let attackers confirm which emails are registered
by firing bulk login attempts.

### Defence in depth
Never claim a system can't be hacked. Reduce likelihood, limit damage:
2FA on all production accounts, short token expiry, key rotation, rate limiting,
CAPTCHA, secrets managers (Vault, AWS Secrets Manager) at larger scale.

### Admin creation pattern
Public registration hardcodes role="customer" server-side. First admin comes
from a seed script (bootstrap problem). Further admins are created only through
an admin-only RBAC-protected endpoint.

### Never trust client input / privilege escalation
Any field the client controls is an attack surface. Security-critical values
(role, prices, balances, is_active) are NEVER accepted from request bodies,
always set server-side. Same principle later: checkout reads prices from the
database, never from the client.

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
without writing validators. Custom validators only for genuinely custom rules
(uppercase, special characters).

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

## Response schemas / response_model

### Why response_model matters (security)
Without a response_model, returning a SQLAlchemy object directly serializes
EVERY column, including hashed_password. response_model = UserResponse on
the endpoint filters the output down to only the declared fields,
automatically, every time.





# INTERVIEW TALKING POINTS

## Architecture decisions

### Customer facing vs admin only routes
Products, orders, cart, users, auth are customer facing. Inventory and payments
are admin only. Designing access control at the architecture stage, not as an
afterthought, shows security thinking.

### Services layer
Routers handle HTTP only, business logic lives in services, one service per
router. Cleaner, testable, maintainable.

### Why order_items exists
Many to many between orders and products. Also captures price_at_purchase so
historical orders are immune to future price changes.

### Inventory as a separate table
Products can have variants (sizes), each with independent stock. Stock inside
the products table cannot model that cleanly.

### Soft delete on products
is_active boolean instead of deleting rows. Preserves history, old orders still
reference valid products.

### Cart in Redis not PostgreSQL
Temporary, high frequency session data belongs in memory. Database is for
permanent records. Much faster cart operations.

## Race conditions and stock locking
Cart add does not reserve stock. At checkout the system locks the inventory row,
checks quantity, exactly one concurrent transaction succeeds. This is how real
time eCommerce handles concurrent purchases at scale. (Will implement in Phase 3.)

## Data integrity

### Numeric over Float for money
Float precision errors (0.1 + 0.2 = 0.30000000000000004) are unacceptable for
money. Numeric(10, 2) is exact. Knowing this distinction matters in fintech
and eCommerce.

## Configuration and security

### Code vs config separation (twelve factor)
Code never knows its environment. The same database.py runs locally, in Docker,
and on Render, only environment variables change. No hardcoded fallbacks, fail
loudly if config is missing.

### Secrets vs local dev config
Local dev credentials (postgres:postgres@localhost) are safe to commit, they
only work on the developer's machine. Secrets (SECRET_KEY, production URLs,
live API keys) live only in .env locally and platform environment variables
in production. I questioned this distinction myself during the build.

### Alembic reads config from environment
No credentials in alembic.ini (it gets committed). env.py overrides
sqlalchemy.url from the environment at runtime.

## Code quality

### models.py vs schemas.py separation
Database layer and API contract layer deliberately separated. Some projects mix
them, separating is cleaner and easier to maintain.

### CORS configured without a frontend
Production standard practice, shows understanding of how APIs serve real
frontends in the wild.

### One models.py vs split files
Deliberate choice for this project size. Know how to split per domain with
__init__.py imports for larger codebases. Structure should match scale.

## Auth and security (Phase 2)

### Hashing vs encryption
Classic interview question. Encryption is reversible by design (key exists),
hashing is one-way by design (no reverse exists). Login compares hashes, never
unhashes. Even the developer cannot read user passwords.

### User enumeration prevention
Login returns the same generic error for wrong email and wrong password.
Different messages let attackers build verified lists of registered emails
from error responses alone. Register endpoint leaks similar info, mitigated
with rate limiting (slowapi in Phase 6), CAPTCHA, or verify-by-email patterns.

### Privilege escalation / never trust client input
role is not a field in RegisterRequest. If it were, any user could send
"role": "admin" and own every admin endpoint. Role is hardcoded server-side.
Same principle protects prices at checkout in Phase 5.

### Admin bootstrap
First admin via seed script (no admin exists yet to create one), further
admins via admin-only RBAC-protected endpoint. Public registration can never
produce an admin.

### Defence in depth mindset
Never say "this can't be hacked". Say "here's how I reduce the chance and
limit the damage": 2FA, short token expiry (30 min), key rotation, separate
keys per environment, rate limiting, secrets managers at scale.

### 401 vs 403
401 = identity unknown (bad/missing token). 403 = identity known, permission
insufficient. Using them correctly signals API literacy.

### Password policy reasoning
Min 8 chars with complexity rules, no low max cap. Long passphrases are
exponentially stronger and hashing makes storage length-independent. Rejecting
a 40-char password is an anti-pattern.

### response_model as a security feature
Declaring response_model = UserResponse on an endpoint isn't just
documentation, it actively strips fields like hashed_password from every
response, even if the endpoint code returns the full ORM object. Defence
in depth applied to outgoing data, not just incoming.

### API layer vs frontend layer (correct mental model)
The API decides what data LEAVES the server (response schemas). The frontend
decides what data gets DISPLAYED to a human (UI code). Saying "the frontend
hides sensitive data" is a red flag, it implies the frontend is a security
boundary, it isn't. Sensitive data should never leave the API in the first
place.

### role in UserResponse, not a secret
role is included in every user response, customer or admin. It's not hidden
from anyone, it's just rarely displayed to customers because there's no UI
reason to. Admins/frontends use it to make UI decisions (show/hide admin
controls), the actual access control is the RBAC check on the backend, the
UI is just UX polish.

### created_at/updated_at, dual purpose
Useful to customers ("member since", "last updated") and essential to admins
for support and fraud investigation (account age vs activity patterns).

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