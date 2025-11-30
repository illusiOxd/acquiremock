from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SuccessFulOperation(SQLModel, table=True):
    __tablename__ = "successful_operations"

    id: Optional[int] = Field(default=None, primary_key=True)
    payment_id: str = Field(index=True, unique=True)
    email: str = Field(index=True)
    amount: float
    reference: str
    card_mask: str
    redirect_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SavedCard(SQLModel, table=True):
    __tablename__ = "saved_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    card_hash: str
    cvv_hash: str
    expiry: str
    card_mask: str
    created_at: datetime = Field(default_factory=datetime.utcnow)