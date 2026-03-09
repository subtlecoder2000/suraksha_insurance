# 📧 Email Agent - SMTP Integration Guide

## 🎉 Your Email Agent Can Now Send REAL Emails!

The Email Agent has been upgraded from stub mode to **production-ready SMTP email sending**.

---

## 🚀 Quick Start (3 Steps)

### **Step 1: Run Setup Wizard**
```bash
cd /home/labuser/Desktop/SUREKHA_INSURANCE
python3 setup_email.py
```

This interactive wizard will:
- Guide you through provider selection (Gmail/Outlook/Custom)
- Help you create app passwords
- Test the connection
- Save credentials to `.env` file
- Send a test email

### **Step 2: Choose Your Provider**

#### **Option A: Gmail (Recommended)**
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to https://myaccount.google.com/apppasswords
4. Create an App Password for "Mail"
5. Copy the 16-character password
6. Enter it in the setup wizard

#### **Option B: Outlook/Office365**
1. Go to https://account.microsoft.com/security
2. Enable **2-Step Verification**
3. Create an App Password
4. Enter it in the setup wizard

#### **Option C: Custom SMTP**
- Enter your SMTP host, port, username, password

#### **Option D: Skip (Stub Mode)**
- Email agent will log to console only (no actual sending)

### **Step 3: Test It!**
```bash
# Restart servers to load new config
pkill -f uvicorn
pkill -f streamlit

# Start backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &

# Start frontend
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
```

Then:
1. Open http://localhost:8501
2. Go to **▶️ Run Journeys (Demo)**
3. Click **"Run Journey A (Rajesh Kumar)"**
4. Check your email inbox! 📬

---

## 📋 Manual Configuration (Alternative)

If you prefer to edit `.env` manually:

```bash
# Add these lines to .env file
SMTP_PROVIDER=gmail
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_NAME=Suraksha Life Insurance

# For custom SMTP (optional)
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
```

---

## 🧪 Testing Email Service

### **Quick Test Script**
```python
from services.email_service import get_email_service

email_service = get_email_service()

# Test connection
result = email_service.test_connection()
print(result)

# Send test email
result = email_service.send_renewal_email(
    customer_name="Test Customer",
    customer_email="your-test-email@example.com",
    policy_number="TEST-001",
    policy_type="Term Life Insurance",
    premium_amount=25000,
    due_date="31 March 2026",
    sum_assured=5000000,
    offers=["10% No-Claim Discount", "₹500 AutoPay Cashback"],
    payment_link="https://pay.suraksha.in/test",
    language="en"
)
print(result)
```

### **Run from Terminal**
```bash
cd /home/labuser/Desktop/SUREKHA_INSURANCE

python3 << 'EOF'
from services.email_service import get_email_service

email_service = get_email_service()

# Test connection
print(email_service.test_connection())

# Send to your email
email_service.send_renewal_email(
    customer_name="Your Name",
    customer_email="your.email@example.com",
    policy_number="TEST-001",
    policy_type="Term Life Insurance",
    premium_amount=25000,
    due_date="31 March 2026",
    sum_assured=5000000,
    offers=["10% Discount", "₹500 Cashback"],
    payment_link="https://pay.suraksha.in/test",
    language="en"
)
EOF
```

---

## 📧 Email Features

### **Beautiful HTML Templates**
- Professional gradient design
- Responsive (mobile-friendly)
- Policy details box
- Highlighted offers section
- Clear call-to-action button
- IRDAI compliance footer

### **Smart Content**
- Personalized greetings
- Dynamic offers based on customer profile
- Urgency indicators (nudge 1/2/3)
- Multi-language support (9 Indian languages)
- Plain text fallback for old email clients

### **Security & Compliance**
- TLS encryption (secure connection)
- App passwords (not regular passwords)
- PII masking in logs
- IRDAI-compliant disclaimers
- Unsubscribe mechanism

---

## 🔍 How It Works

### **Previous (Stub Mode)**
```python
def send_email(...):
    print(f"📧 [STUB] Email sent to {email}")
    # Nothing actually sent
```

### **Now (Real SMTP)**
```python
def send_email(...):
    # Generate beautiful HTML email
    html = email_service._generate_renewal_template(...)
    
    # Actually send via SMTP
    result = email_service.send_email(
        to_email=customer_email,
        subject=subject,
        body_html=html
    )
    
    # Returns delivery status
    # {'success': True, 'message_id': '...', 'provider': 'gmail'}
```

### **Integration Points**
```
Orchestrator
    ↓
Email Agent (agents/email_agent.py)
    ↓
Email Service (services/email_service.py)
    ↓
SMTP Server (Gmail/Outlook/Custom)
    ↓
Customer's Inbox ✅
```

---

## 📊 Monitoring & Logs

### **Success Logs**
```
✅ Email sent successfully to rajesh.kumar@example.com
   Provider: gmail
   Message ID: <1234567890@renewai.suraksha.com>
   Subject: 🔔 Renew Your Term Life Insurance - Exclusive Offers Inside!
```

### **Error Logs**
```
❌ Email FAILED to invalid@example.com
   Error: authentication_failed
   Message: Invalid SMTP credentials. Check username/password.
```

### **Stub Mode Logs**
```
📧 EMAIL STUB MODE (No SMTP credentials configured)
To: customer@example.com
From: Suraksha Life Insurance <not-configured@example.com>
Subject: Your policy renewal is coming up
Body Preview: Dear Rajesh, Your Term policy is due for renewal...
```

---

## 🛠️ Troubleshooting

### **Issue: "Authentication Failed"**
**Solution:**
- For Gmail: Use App Password, NOT regular password
- Enable 2-Step Verification first
- Regenerate app password if needed

### **Issue: "Connection Timeout"**
**Solution:**
- Check firewall settings
- Verify SMTP host and port
- Try port 465 (SSL) instead of 587 (TLS)

### **Issue: "Emails Not Arriving"**
**Solution:**
- Check spam/junk folder
- Verify recipient email address
- Check email service logs for errors
- Test with a different email address

### **Issue: "Still in Stub Mode"**
**Solution:**
- Ensure `.env` has SMTP credentials
- Restart FastAPI and Streamlit servers
- Check logs for "Email service initialized with GMAIL SMTP"

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Use dedicated email account (e.g., renewals@suraksha.com)
- [ ] Configure SPF, DKIM, DMARC records for domain
- [ ] Set up email tracking (opens, clicks)
- [ ] Implement rate limiting (avoid spam filters)
- [ ] Add retry logic for failed sends
- [ ] Monitor bounce rates
- [ ] Set up webhook for delivery status
- [ ] Enable email queue for bulk sending
- [ ] Add unsubscribe management
- [ ] Compliance review (IRDAI, DPDPA)

---

## 📚 API Reference

### **EmailService Class**

```python
class EmailService:
    def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict
    
    def send_renewal_email(
        customer_name: str,
        customer_email: str,
        policy_number: str,
        policy_type: str,
        premium_amount: int,
        due_date: str,
        sum_assured: int,
        offers: List[str],
        payment_link: str,
        language: str = 'en'
    ) -> Dict
    
    def test_connection() -> Dict
```

### **Return Values**

**Success:**
```python
{
    'success': True,
    'message_id': '<1234@renewai.suraksha.com>',
    'to': 'customer@example.com',
    'subject': 'Renew Your Policy...',
    'sent_at': '2026-03-06T10:30:00',
    'provider': 'gmail',
    'status': 'delivered'
}
```

**Failure:**
```python
{
    'success': False,
    'error': 'authentication_failed',
    'message': 'Invalid SMTP credentials',
    'details': 'SMTPAuthenticationError: ...'
}
```

---

## 🚀 Next Steps

Now that email is working, you can:

1. **Test with Real Data**: Run journeys and check actual email delivery
2. **Add WhatsApp**: Set up Twilio integration next
3. **Monitor Performance**: Track open rates, click rates
4. **A/B Testing**: Try different subject lines, templates
5. **Scale Up**: Configure bulk email sending

---

## 💡 Pro Tips

1. **Gmail Daily Limit**: 500 emails/day for regular accounts, 2000/day for Google Workspace
2. **Subject Lines**: Keep under 50 characters for mobile display
3. **Preview Text**: First 100 characters show in inbox preview
4. **Images**: Host images externally (don't embed large files)
5. **Links**: Use UTM parameters for tracking
6. **Testing**: Always send to yourself first!

---

## 📞 Support

If you need help:
1. Check logs in terminal
2. Run `python3 setup_email.py` again
3. Test connection: `email_service.test_connection()`
4. Verify `.env` file has correct credentials

**Remember**: The system works in stub mode without configuration - you'll see logs but no emails sent. Configure SMTP to enable real sending!

---

## ✅ Summary

**Before**: Email agent logged to console only (stub mode)  
**After**: Email agent sends REAL emails via SMTP to actual inboxes! 📧✨

**To activate**: Run `python3 setup_email.py` and follow the wizard.

**Enjoy your fully functional Email Agent!** 🎉
