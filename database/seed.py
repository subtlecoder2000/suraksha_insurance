"""
Seed database with demo data from existing CRM
Migrates JSON-like structures to SQLAlchemy models
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import SessionLocal, init_database
from database.models import Customer, ObjectionResponse, Scorecard
from data.crm import get_all_policyholders
from data.objection_library import OBJECTION_LIBRARY


def seed_customers(db):
    """Seed customers from existing CRM data"""
    print("\n📊 Seeding customers...")
    
    policyholders = get_all_policyholders()
    
    for ph in policyholders:
        customer = Customer(
            customer_id=ph.policy_id,
            name=ph.name,
            age=ph.age,
            gender="Male",  # Default, could be enhanced
            city="Mumbai",  # Default
            state=ph.state,
            
            policy_number=ph.policy_number,
            policy_type=ph.policy_type,
            sum_assured=int(ph.sum_assured),
            annual_premium=int(ph.annual_premium),
            payment_mode=ph.payment_mode,
            policy_start_date=ph.renewal_due_date - timedelta(days=365 * ph.years_as_customer),
            due_date=ph.renewal_due_date,
            grace_period_end=ph.renewal_due_date + timedelta(days=30),
            
            persistency_score=0.75 if ph.lapse_risk == "Low" else (0.50 if ph.lapse_risk == "Medium" else 0.30),
            propensity_to_lapse=0.15 if ph.lapse_risk == "Low" else (0.30 if ph.lapse_risk == "Medium" else 0.50),
            lifetime_value=int(ph.annual_premium * 10),
            
            preferred_language=ph.language,
            preferred_channel=ph.preferred_channel,
            preferred_time=ph.preferred_time_window,
            
            current_journey_stage="T-45",
            last_contact_date=datetime.utcnow() - timedelta(days=5),
            renewal_status="PENDING" if ph.last_payment_status == "Pending" else "RENEWED",
            
            mobile=ph.phone,
            email=ph.email,
            whatsapp_opt_in=True,
        )
        
        db.add(customer)
    
    db.commit()
    print(f"✅ Seeded {len(policyholders)} customers")


def seed_objections(db):
    """Seed objection library"""
    print("\n📚 Seeding objection responses...")
    
    for obj_entry in OBJECTION_LIBRARY:
        objection = ObjectionResponse(
            objection_type=obj_entry.id,
            category=obj_entry.category,
            response_english=obj_entry.response if obj_entry.language == "English" else "",
            response_hindi=obj_entry.response if obj_entry.language == "Hindi" else "",
            response_tamil=obj_entry.response if obj_entry.language == "Tamil" else "",
            response_telugu=obj_entry.response if obj_entry.language == "Telugu" else "",
            usage_count=0,
            success_rate=0.78,
            is_active=True
        )
        
        db.add(objection)
    
    db.commit()
    print(f"✅ Seeded {len(OBJECTION_LIBRARY)} objection responses")


def seed_initial_scorecard(db):
    """Create initial scorecard entry"""
    print("\n📈 Seeding initial scorecard...")
    
    scorecard = Scorecard(
        date=datetime.utcnow(),
        persistency_rate=0.71,
        cost_per_renewal=182.0,
        ai_automation_rate=0.0,  # Will increase as system runs
        human_escalation_rate=1.0,  # Currently 100%
        
        email_open_rate=0.18,
        whatsapp_response_rate=0.0,
        voice_conversion_rate=0.0,
        
        critique_pass_rate=0.0,
        nps_score=34.0,
        
        total_renewals=0,
        total_revenue=0,
        total_cost=0,
        cost_savings=0,
        
        avg_escalation_time_hours=0.0,
        distress_sla_met_percent=0.0
    )
    
    db.add(scorecard)
    db.commit()
    print("✅ Seeded initial scorecard")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 PROJECT RenewAI - Database Seeding")
    print("=" * 60)
    
    # Initialize database (create tables)
    init_database()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing_customers = db.query(Customer).count()
        if existing_customers > 0:
            print(f"\n⚠️  Database already has {existing_customers} customers")
            response = input("Do you want to clear and re-seed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return
            
            # Clear existing data
            print("\n🗑️  Clearing existing data...")
            db.query(Scorecard).delete()
            db.query(ObjectionResponse).delete()
            db.query(Customer).delete()
            db.commit()
            print("✅ Cleared existing data")
        
        # Seed data
        seed_customers(db)
        seed_objections(db)
        seed_initial_scorecard(db)
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SEEDING COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - Customers: {db.query(Customer).count()}")
        print(f"   - Objection Responses: {db.query(ObjectionResponse).count()}")
        print(f"   - Scorecard Entries: {db.query(Scorecard).count()}")
        print(f"\n🗄️  Database location: renewai.db")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
