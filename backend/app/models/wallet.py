from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from sqlalchemy import Column, Numeric, DateTime


class Wallet(SQLModel, table=True):
    __tablename__ = 'wallets'  # Лучше использовать множественное число для таблиц

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, sa_column_kwargs={"unique": True})
    balance: Decimal = Field(default=Decimal('0.00'),
                             sa_column=Column(Numeric(10, 2)), description="Текущий баланс в RUB")
    currency: str = Field(default="RUB", max_length=3)
    is_active: bool = Field(default=True)

    # Связи
    user_id: int = Field(foreign_key="services.id")  # Предполагается, что таблица пользователей называется 'users'
    user: "User" = Relationship(back_populates="wallet")

    transactions: List["Transaction"] = Relationship(
        back_populates="wallet",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class WalletCreate(BaseModel):
    user_id: int

class WalletUpdate(BaseModel):
    pass







class TransactionType(str, Enum):
    DEPOSIT = "deposit"       # Пополнение
    WITHDRAW = "withdraw"     # Вывод средств
    TRANSFER = "transfer"     # Перевод между пользователями
    REFUND = "refund"         # Возврат платежа
    CASHBACK = "cashback"


class StatusPay(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"




class Transaction(SQLModel, table=True):
    __tablename__ = 'transactions'

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, sa_column_kwargs={"unique": True})
    amount: Decimal = Field(
        sa_column=Column(Numeric(10, 2)),
        description="Сумма (отрицательная для списаний)"
    )
    type: TransactionType = Field(
        default=TransactionType.DEPOSIT,
        sa_type=sa.Enum(TransactionType),
        description="Тип транзакции"
    )
    status: StatusPay = Field(
        sa_type=sa.Enum(StatusPay),
        description="Состояние платежа"
    )
    transaction_id: Optional[str] = Field(
        default=None,
        description="ID платежа в Stripe/другой системе"
    )
    signature: Optional[str] = Field(
        default=None,
        description="Подпись транзакции для верификации"
    )
    extra_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Дополнительные данные (например, booking_id, user_id, stadium_owner_id)"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True))
    )

    # Связи
    wallet_id: UUID = Field(foreign_key="wallets.id")
    wallet: "Wallet" = Relationship(back_populates="transactions")


class TransactionCreate(BaseModel):
    amount:Decimal
    type: TransactionType
    status: StatusPay

class TransactionUpdate(BaseModel):
    pass