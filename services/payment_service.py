from sqlalchemy.orm import Session
from models.models import PaymentModel
from decimal import Decimal

def create_payment(db: Session, order_id: int, amount: Decimal, payment_method: str):
    payment = PaymentModel(order_id=order_id, amount=amount, status="pending", payment_method = payment_method)
    db.add(payment)
