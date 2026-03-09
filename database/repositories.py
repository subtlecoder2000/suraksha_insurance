"""
Repository pattern for database operations
Provides clean interface to access data without exposing SQLAlchemy details
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .models import (
    Customer, Conversation, ObjectionResponse, 
    LoyaltyOffer, EscalationCase, AuditLog, Scorecard
)


class CustomerRepository:
    """Customer data access layer"""
    
    @staticmethod
    def get_all(db: Session) -> List[Customer]:
        """Get all customers"""
        return db.query(Customer).all()
    
    @staticmethod
    def get_by_id(db: Session, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    @staticmethod
    def get_renewal_pipeline(db: Session) -> List[Customer]:
        """Get customers in renewal pipeline (not renewed yet)"""
        return db.query(Customer).filter(
            Customer.renewal_status.in_(["PENDING", "IN_GRACE"])
        ).all()
    
    @staticmethod
    def get_by_journey_stage(db: Session, stage: str) -> List[Customer]:
        """Get customers at specific journey stage"""
        return db.query(Customer).filter(Customer.current_journey_stage == stage).all()
    
    @staticmethod
    def update_journey_stage(db: Session, customer_id: str, stage: str):
        """Update customer journey stage"""
        customer = CustomerRepository.get_by_id(db, customer_id)
        if customer:
            customer.current_journey_stage = stage
            customer.last_contact_date = datetime.utcnow()
            customer.updated_at = datetime.utcnow()
            db.commit()
            return customer
        return None
    
    @staticmethod
    def mark_renewed(db: Session, customer_id: str):
        """Mark customer as renewed"""
        customer = CustomerRepository.get_by_id(db, customer_id)
        if customer:
            customer.renewal_status = "RENEWED"
            customer.updated_at = datetime.utcnow()
            db.commit()
            return customer
        return None
    
    @staticmethod
    def get_high_risk_customers(db: Session, threshold: float = 0.3) -> List[Customer]:
        """Get customers with high lapse propensity"""
        return db.query(Customer).filter(
            Customer.propensity_to_lapse >= threshold
        ).order_by(desc(Customer.propensity_to_lapse)).all()


class ConversationRepository:
    """Conversation history data access layer"""
    
    @staticmethod
    def create(db: Session, conversation_data: dict) -> Conversation:
        """Create new conversation record"""
        conversation = Conversation(**conversation_data)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def get_by_customer(db: Session, customer_id: str) -> List[Conversation]:
        """Get all conversations for a customer"""
        return db.query(Conversation).filter(
            Conversation.customer_id == customer_id
        ).order_by(Conversation.timestamp).all()
    
    @staticmethod
    def get_recent(db: Session, customer_id: str, limit: int = 5) -> List[Conversation]:
        """Get recent conversations for a customer"""
        return db.query(Conversation).filter(
            Conversation.customer_id == customer_id
        ).order_by(desc(Conversation.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_sentiment_summary(db: Session, customer_id: str) -> dict:
        """Get sentiment distribution for customer"""
        conversations = ConversationRepository.get_by_customer(db, customer_id)
        total = len(conversations)
        if total == 0:
            return {"positive": 0, "neutral": 0, "negative": 0}
        
        positive = sum(1 for c in conversations if c.sentiment == "POSITIVE")
        negative = sum(1 for c in conversations if c.sentiment == "NEGATIVE")
        neutral = total - positive - negative
        
        return {
            "positive": positive / total,
            "neutral": neutral / total,
            "negative": negative / total
        }


class ObjectionRepository:
    """Objection library data access layer"""
    
    @staticmethod
    def get_all(db: Session) -> List[ObjectionResponse]:
        """Get all objection responses"""
        return db.query(ObjectionResponse).filter(ObjectionResponse.is_active == True).all()
    
    @staticmethod
    def get_by_type(db: Session, objection_type: str) -> Optional[ObjectionResponse]:
        """Get response for specific objection type"""
        return db.query(ObjectionResponse).filter(
            ObjectionResponse.objection_type == objection_type,
            ObjectionResponse.is_active == True
        ).first()
    
    @staticmethod
    def get_by_category(db: Session, category: str) -> List[ObjectionResponse]:
        """Get responses by category"""
        return db.query(ObjectionResponse).filter(
            ObjectionResponse.category == category,
            ObjectionResponse.is_active == True
        ).all()
    
    @staticmethod
    def increment_usage(db: Session, objection_id: int):
        """Increment usage count for an objection"""
        objection = db.query(ObjectionResponse).filter(ObjectionResponse.id == objection_id).first()
        if objection:
            objection.usage_count += 1
            db.commit()


class EscalationRepository:
    """Escalation queue data access layer"""
    
    @staticmethod
    def create(db: Session, escalation_data: dict) -> EscalationCase:
        """Create new escalation case"""
        escalation = EscalationCase(**escalation_data)
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        return escalation
    
    @staticmethod
    def get_pending(db: Session) -> List[EscalationCase]:
        """Get all pending escalations"""
        return db.query(EscalationCase).filter(
            EscalationCase.status == "PENDING"
        ).order_by(EscalationCase.created_at).all()
    
    @staticmethod
    def get_by_priority(db: Session, priority: str) -> List[EscalationCase]:
        """Get escalations by priority"""
        return db.query(EscalationCase).filter(
            EscalationCase.priority == priority,
            EscalationCase.status != "CLOSED"
        ).all()
    
    @staticmethod
    def assign_case(db: Session, case_id: int, assigned_to: str):
        """Assign escalation case to a team"""
        case = db.query(EscalationCase).filter(EscalationCase.id == case_id).first()
        if case:
            case.assigned_to = assigned_to
            case.assigned_at = datetime.utcnow()
            case.status = "IN_PROGRESS"
            db.commit()
            return case
        return None
    
    @staticmethod
    def resolve_case(db: Session, case_id: int, resolution: str):
        """Mark case as resolved"""
        case = db.query(EscalationCase).filter(EscalationCase.id == case_id).first()
        if case:
            case.status = "RESOLVED"
            case.resolution = resolution
            case.resolved_at = datetime.utcnow()
            case.sla_met = case.resolved_at <= case.sla_deadline if case.sla_deadline else True
            db.commit()
            return case
        return None


class AuditLogRepository:
    """Audit log data access layer"""
    
    @staticmethod
    def create(db: Session, log_data: dict) -> AuditLog:
        """Create audit log entry"""
        audit_log = AuditLog(**log_data)
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    
    @staticmethod
    def get_all(db: Session, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        return db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_irdai_relevant(db: Session) -> List[AuditLog]:
        """Get IRDAI-relevant logs"""
        return db.query(AuditLog).filter(
            AuditLog.irdai_relevant == True
        ).order_by(desc(AuditLog.timestamp)).all()
    
    @staticmethod
    def get_by_customer(db: Session, customer_id: str) -> List[AuditLog]:
        """Get audit logs for specific customer"""
        return db.query(AuditLog).filter(
            AuditLog.customer_id == customer_id
        ).order_by(desc(AuditLog.timestamp)).all()


class ScorecardRepository:
    """Scorecard metrics data access layer"""
    
    @staticmethod
    def get_latest(db: Session) -> Optional[Scorecard]:
        """Get latest scorecard"""
        return db.query(Scorecard).order_by(desc(Scorecard.date)).first()
    
    @staticmethod
    def get_by_date_range(db: Session, start_date: datetime, end_date: datetime) -> List[Scorecard]:
        """Get scorecards within date range"""
        return db.query(Scorecard).filter(
            Scorecard.date >= start_date,
            Scorecard.date <= end_date
        ).order_by(Scorecard.date).all()
    
    @staticmethod
    def update_or_create(db: Session, scorecard_data: dict) -> Scorecard:
        """Update existing scorecard or create new one for today"""
        today = datetime.utcnow().date()
        scorecard = db.query(Scorecard).filter(
            func.date(Scorecard.date) == today
        ).first()
        
        if scorecard:
            for key, value in scorecard_data.items():
                setattr(scorecard, key, value)
        else:
            scorecard = Scorecard(**scorecard_data)
            db.add(scorecard)
        
        db.commit()
        db.refresh(scorecard)
        return scorecard
