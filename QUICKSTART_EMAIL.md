# 📧 Email Agent - Quick Start Guide

## 🎯 What's New?

Your Email Agent can now **send REAL emails** via SMTP! No more stub mode logs - actual emails delivered to inboxes.

---

## ⚡ 3-Step Setup

### **Step 1: Run Setup Wizard**
```bash
python3 setup_email.py
```

### **Step 2: Follow On-Screen Instructions**
- Choose Gmail (recommended) or Outlook
- Create App Password (not your regular password!)
- Enter credentials when prompted
- Test connection

### **Step 3: Test It!**
```bash
# Go to dashboard
# Run Journey A
# Check email inbox!
```

---

## 🔑 Gmail App Password (5 Minutes)

1. **Enable 2-Step Verification**
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification" → Turn On

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select: Mail + Other (Custom name)
   - Name it: "RenewAI"
   - Click "Generate"

3. **Copy Password**
   - You'll get 16 characters (e.g., `abcd efgh ijkl mnop`)
   - Copy this (spaces don't matter)

4. **Paste in Setup Wizard**
   - Run `python3 setup_email.py`
   - Paste when prompted
   - Done! ✅

---

## 📧 What You Get

### **Beautiful HTML Emails**
✅ Professional design with gradient headers  
✅ Policy details in highlighted box  
✅ Loyalty offers section  
✅ Clear "Pay Now" button  
✅ Mobile responsive  
✅ IRDAI compliance footer  

### **Smart Personalization**
✅ Customer name in greeting  
✅ Policy-specific details  
✅ Dynamic offers based on tenure  
✅ Urgency indicators (T-45, T-30, T-10)  
✅ Multi-language support (9 languages)  

### **Production Ready**
✅ Real SMTP delivery  
✅ Error handling & retries  
✅ Delivery status tracking  
✅ Secure TLS encryption  
✅ Audit logging  

---

## 🧪 Test Email Template

When you run the setup wizard, you'll see this test email:

**Subject:** 🔔 Renew Your Term Life Insurance - Exclusive Offers Inside!

**Body Preview:**
```
Dear Test Customer,

Your Term Life Insurance policy is due for renewal on 31 March 2026.
We've been protecting your family's future together!

Policy Number: TEST-001
Coverage: ₹50,00,000
Annual Premium: ₹25,000

🎉 Special Renewal Offers for You
✅ 10% No-Claim Discount - Save ₹2,500
✅ ₹500 AutoPay Cashback
✅ Premium Holiday - Skip 1 month after renewal

[Pay Now & Renew Button]
```

---

## 🚀 Try It Now!

### **Option A: Use Setup Wizard (Easiest)**
```bash
python3 setup_email.py
```

### **Option B: Manual .env Edit**
```bash
# Add to .env file:
SMTP_PROVIDER=gmail
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_NAME=Suraksha Life Insurance
```

### **Option C: Skip (Stay in Stub Mode)**
- Email agent will log to console
- No actual emails sent
- Good for testing without email account

---

## 📊 Status Check

Run this anytime to check configuration:
```bash
python3 -c "from services.email_service import get_email_service; s=get_email_service(); print(f'Mode: {\"LIVE\" if not s.stub_mode else \"STUB\"}')"
```

---

## 🎉 Success Indicators

When configured correctly, you'll see:
```
✅ Email service initialized with GMAIL SMTP
✅ Email DELIVERED to customer@example.com via gmail
🎯 Message ID: <1234567890@renewai.suraksha.com>
```

In stub mode, you'll see:
```
⚠️  SMTP credentials not configured. Email sending will be in STUB mode.
📧 EMAIL STUB MODE (No SMTP credentials configured)
```

---

## ❓ Need Help?

**Q: "Authentication Failed"**  
A: Use App Password (not regular password). Enable 2FA first.

**Q: "Email not arriving"**  
A: Check spam folder. Verify email address. Check logs.

**Q: "Still in stub mode"**  
A: Restart servers after configuring. Check .env file.

**Q: "Want to test without real email"**  
A: Don't configure SMTP. Stub mode logs to console.

---

## 📚 Full Documentation

- **Setup Guide**: `EMAIL_SETUP_GUIDE.md`
- **Service Code**: `services/email_service.py`
- **Agent Code**: `agents/email_agent.py`

---

## 🎬 Next Steps

1. ✅ Run `python3 setup_email.py`
2. ✅ Configure Gmail/Outlook credentials
3. ✅ Send test email
4. ✅ Restart servers
5. ✅ Run Journey A from dashboard
6. ✅ Check your inbox!

**Your Email Agent is ready to go LIVE!** 📧✨
