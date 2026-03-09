"""
Database package for PROJECT RenewAI
Provides SQLAlchemy models and database session management
"""

from .connection import engine, SessionLocal, get_db, init_database
from .models import (
    Customer,
    Conversation,
    ObjectionResponse,
    LoyaltyOffer,
    EscalationCase,
    AuditLog,
    Scorecard
)

__all__ = [
    "engine",
    "SessionLocal", 
    "get_db",
    "init_database",
    "Customer",
    "Conversation",
    "ObjectionResponse",
    "LoyaltyOffer",
    "EscalationCase",
    "AuditLog",
    "Scorecard"
]
