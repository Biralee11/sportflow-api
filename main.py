from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, products_router, inventory_router, cart_router, orders_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(inventory_router.router)
app.include_router(cart_router.router)
app.include_router(orders_router.router)

@app.get("/")
def root():
    return{"message": "SportFlow API is running"}