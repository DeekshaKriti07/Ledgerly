from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from app.database import Base

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    full_name: Mapped[str]=mapped_column(String(120))
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(30),default="Accountant")
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Account(Base):
    __tablename__="accounts"
    code: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(120),unique=True)
    category: Mapped[str]=mapped_column(String(30))
    normal_balance: Mapped[str]=mapped_column(String(10))

class Vendor(Base):
    __tablename__="vendors"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(180),index=True)
    gstin: Mapped[str|None]=mapped_column(String(20),nullable=True)
    email: Mapped[str|None]=mapped_column(String(255),nullable=True)
    payment_terms: Mapped[str]=mapped_column(String(40),default="Net 30")

class Customer(Base):
    __tablename__="customers"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(180),index=True)
    gstin: Mapped[str|None]=mapped_column(String(20),nullable=True)
    email: Mapped[str|None]=mapped_column(String(255),nullable=True)

class Invoice(Base):
    __tablename__="invoices"
    id: Mapped[int]=mapped_column(primary_key=True)
    invoice_no: Mapped[str]=mapped_column(String(80),index=True)
    vendor_id: Mapped[int|None]=mapped_column(ForeignKey("vendors.id"),nullable=True)
    invoice_date: Mapped[date]=mapped_column(Date)
    due_date: Mapped[date|None]=mapped_column(Date,nullable=True)
    subtotal: Mapped[float]=mapped_column(Float)
    tax: Mapped[float]=mapped_column(Float,default=0)
    total: Mapped[float]=mapped_column(Float)
    status: Mapped[str]=mapped_column(String(30),default="Pending")
    vendor: Mapped[Vendor|None]=relationship()

class JournalEntry(Base):
    __tablename__="journal_entries"
    id: Mapped[int]=mapped_column(primary_key=True)
    entry_no: Mapped[str]=mapped_column(String(30),unique=True,index=True)
    entry_date: Mapped[date]=mapped_column(Date)
    description: Mapped[str]=mapped_column(String(300))
    created_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    status: Mapped[str]=mapped_column(String(20),default="Posted")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    lines: Mapped[list["JournalLine"]]=relationship(cascade="all, delete-orphan",back_populates="entry")

class JournalLine(Base):
    __tablename__="journal_lines"
    id: Mapped[int]=mapped_column(primary_key=True)
    entry_id: Mapped[int]=mapped_column(ForeignKey("journal_entries.id"))
    account_code: Mapped[int]=mapped_column(ForeignKey("accounts.code"))
    debit: Mapped[float]=mapped_column(Float,default=0)
    credit: Mapped[float]=mapped_column(Float,default=0)
    entry: Mapped[JournalEntry]=relationship(back_populates="lines")

class BankTransaction(Base):
    __tablename__="bank_transactions"
    id: Mapped[int]=mapped_column(primary_key=True)
    txn_date: Mapped[date]=mapped_column(Date)
    description: Mapped[str]=mapped_column(String(300))
    debit: Mapped[float]=mapped_column(Float,default=0)
    credit: Mapped[float]=mapped_column(Float,default=0)
    reference: Mapped[str|None]=mapped_column(String(100),nullable=True)
    status: Mapped[str]=mapped_column(String(20),default="Unmatched")

class Expense(Base):
    __tablename__="expenses"
    id: Mapped[int]=mapped_column(primary_key=True)
    expense_date: Mapped[date]=mapped_column(Date)
    category: Mapped[str]=mapped_column(String(100))
    amount: Mapped[float]=mapped_column(Float)
    employee: Mapped[str]=mapped_column(String(120))
    status: Mapped[str]=mapped_column(String(20),default="Pending")

class PeriodLock(Base):
    __tablename__="period_locks"
    id: Mapped[int]=mapped_column(primary_key=True)
    period: Mapped[str]=mapped_column(String(7),unique=True)
    locked_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    locked_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
