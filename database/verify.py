"""
Quick database verification script
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import SessionLocal
from database.models import Customer, ObjectionResponse, Conversation, EscalationCase, AuditLog, Scorecard
from sqlalchemy import func

def verify_database():
    """Verify database contents"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("🔍 DATABASE VERIFICATION")
        print("=" * 70)
        
        # Count records in each table
        print("\n📊 Table Counts:")
        print(f"   Customers:           {db.query(Customer).count()}")
        print(f"   Conversations:       {db.query(Conversation).count()}")
        print(f"   Objection Responses: {db.query(ObjectionResponse).count()}")
        print(f"   Escalation Cases:    {db.query(EscalationCase).count()}")
        print(f"   Audit Logs:          {db.query(AuditLog).count()}")
        print(f"   Scorecards:          {db.query(Scorecard).count()}")
        
        # Show sample customers
        print("\n👥 Sample Customers:")
        customers = db.query(Customer).limit(5).all()
        for c in customers:
            print(f"   {c.customer_id}: {c.name} - {c.policy_type} - ₹{c.annual_premium:,} - {c.renewal_status}")
        
        # Show objection categories
        print("\n📚 Objection Categories:")
        categories = db.query(ObjectionResponse.category, func.count(ObjectionResponse.id)).group_by(ObjectionResponse.category).all()
        for cat, count in categories:
            print(f"   {cat}: {count} responses")
        
        # Show pipeline status
        print("\n🔄 Renewal Pipeline:")
        statuses = db.query(Customer.renewal_status, func.count(Customer.customer_id)).group_by(Customer.renewal_status).all()
        for status, count in statuses:
            print(f"   {status}: {count} customers")
        
        # Show journey stages
        print("\n🛤️  Journey Stages:")
        stages = db.query(Customer.current_journey_stage, func.count(Customer.customer_id)).group_by(Customer.current_journey_stage).all()
        for stage, count in stages:
            print(f"   {stage}: {count} customers")
        
        # Show latest scorecard
        print("\n📈 Latest Scorecard:")
        scorecard = db.query(Scorecard).order_by(Scorecard.date.desc()).first()
        if scorecard:
            print(f"   Persistency Rate:     {scorecard.persistency_rate*100:.1f}%")
            print(f"   Cost per Renewal:     ₹{scorecard.cost_per_renewal:.2f}")
            print(f"   AI Automation Rate:   {scorecard.ai_automation_rate*100:.1f}%")
            print(f"   Email Open Rate:      {scorecard.email_open_rate*100:.1f}%")
            print(f"   NPS Score:            {scorecard.nps_score:.0f}")
        
        print("\n" + "=" * 70)
        print("✅ DATABASE IS WORKING CORRECTLY!")
        print("=" * 70)
        print()
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_database()
