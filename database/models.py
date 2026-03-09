"""
SQLAlchemy Database Models for PROJECT RenewAI
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base


class Customer(Base):
    """Customer/Policyholder table"""
    __tablename__ = "customers"
    
    customer_id = Column(String(20), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    city = Column(String(50))
    state = Column(String(50))
    
    # Policy details
    policy_number = Column(String(20), unique=True, index=True)
    policy_type = Column(String(50))
    sum_assured = Column(Integer)
    annual_premium = Column(Integer)
    payment_mode = Column(String(20))  # Annual, Half-yearly, Quarterly, Monthly
    policy_start_date = Column(DateTime)
    due_date = Column(DateTime)
    grace_period_end = Column(DateTime)
    
    # Scoring
    persistency_score = Column(Float)
    propensity_to_lapse = Column(Float)
    lifetime_value = Column(Integer)
    
    # Preferences
    preferred_language = Column(String(20))
    preferred_channel = Column(String(20))
    preferred_time = Column(String(20))
    
    # Journey tracking
    current_journey_stage = Column(String(20))  # T-45, T-30, T-20, T-10, T-5, POST_LAPSE
    last_contact_date = Column(DateTime)
    renewal_status = Column(String(20))  # PENDING, RENEWED, LAPSED, IN_GRACE
    
    # Contact info
    mobile = Column(String(15))
    email = Column(String(100))
    whatsapp_opt_in = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    escalations = relationship("EscalationCase", back_populates="customer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="customer", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation history - semantic memory"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), index=True)
    
    # Conversation details
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    channel = Column(String(20))  # Email, WhatsApp, Voice
    direction = Column(String(10))  # OUTBOUND, INBOUND
    agent = Column(String(50))  # Orchestrator, EmailAgent, WhatsAppAgent, VoiceAgent
    
    # Message content
    message = Column(Text)
    response = Column(Text, nullable=True)
    
    # Sentiment & objections
    sentiment = Column(String(20))  # POSITIVE, NEUTRAL, NEGATIVE
    objections_raised = Column(JSON)  # List of objection types
    objections_resolved = Column(Boolean, default=False)
    
    # Critique results
    critique_passed = Column(Boolean, default=True)
    critique_score = Column(Float)
    critique_issues = Column(JSON, nullable=True)
    
    # Journey context
    journey_stage = Column(String(20))
    outcome = Column(String(50))  # DELIVERED, READ, RESPONDED, NO_RESPONSE, ESCALATED
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")


class ObjectionResponse(Base):
    """Objection library - pre-scripted responses"""
    __tablename__ = "objection_responses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    objection_type = Column(String(50), index=True)
    category = Column(String(50))  # PREMIUM, FINANCIAL, INVESTMENT, CLAIMS, LAPSE
    
    # Multilingual responses
    response_english = Column(Text)
    response_hindi = Column(Text)
    response_tamil = Column(Text, nullable=True)
    response_telugu = Column(Text, nullable=True)
    
    # Metadata
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoyaltyOffer(Base):
    """Dynamic loyalty offers generated for customers"""
    __tablename__ = "loyalty_offers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), index=True)
    
    # Offer details
    offer_type = Column(String(50))  # NO_CLAIM_DISCOUNT, AUTOPAY_CASHBACK, PREMIUM_HOLIDAY, LOYALTY_BONUS
    discount_percent = Column(Float)
    cashback_amount = Column(Integer)
    description = Column(Text)
    
    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_redeemed = Column(Boolean, default=False)
    redeemed_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class EscalationCase(Base):
    """Human escalation queue"""
    __tablename__ = "escalation_cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), index=True)
    
    # Escalation details
    reason = Column(String(50))  # DISTRESS, HNI, COMPLIANCE, REVIVAL, SYSTEM_FAILURE
    priority = Column(String(20))  # CRITICAL, HIGH, MEDIUM, LOW
    category = Column(String(50))
    description = Column(Text)
    
    # Assignment
    assigned_to = Column(String(50))  # RENEWAL_SPECIALIST, SENIOR_RM, BEREAVEMENT_HANDLER, etc.
    assigned_at = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="PENDING")  # PENDING, IN_PROGRESS, RESOLVED, CLOSED
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # SLA tracking
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sla_deadline = Column(DateTime)
    sla_met = Column(Boolean, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="escalations")


class AuditLog(Base):
    """IRDAI compliance audit trail"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), index=True, nullable=True)
    
    # Action tracking
    agent = Column(String(50))
    action = Column(String(100))
    channel = Column(String(20))
    journey_stage = Column(String(20))
    
    # Compliance flags
    irdai_relevant = Column(Boolean, default=False, index=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Data & context
    event_data = Column(JSON)
    
    # Relationships
    customer = relationship("Customer", back_populates="audit_logs")


class Scorecard(Base):
    """Daily scorecard metrics - time series"""
    __tablename__ = "scorecards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, index=True, unique=True)
    
    # Business metrics
    persistency_rate = Column(Float)
    cost_per_renewal = Column(Float)
    ai_automation_rate = Column(Float)
    human_escalation_rate = Column(Float)
    
    # Channel metrics
    email_open_rate = Column(Float)
    whatsapp_response_rate = Column(Float)
    voice_conversion_rate = Column(Float)
    
    # Quality metrics
    critique_pass_rate = Column(Float)
    nps_score = Column(Float)
    
    # Financial metrics
    total_renewals = Column(Integer)
    total_revenue = Column(Integer)
    total_cost = Column(Integer)
    cost_savings = Column(Integer)
    
    # SLA metrics
    avg_escalation_time_hours = Column(Float)
    distress_sla_met_percent = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
