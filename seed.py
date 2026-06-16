from database import SessionLocal
from models.models import UserModel
from services.auth_service import hash_password

db = SessionLocal()
try:
    hashed_password = hash_password("B123456@")
    user = UserModel(email="bira@gmail.com", hashed_password=hashed_password, first_name="Eyebira", last_name="Odugba", role="admin")
    db.add(user)
    db.commit()
    print("Admin user created successfully")
finally:
    db.close()