#!/usr/bin/env python3
"""
setup_email.py
Interactive setup wizard for SMTP email configuration

This will guide you through:
1. Choosing email provider (Gmail/Outlook/Custom)
2. Entering credentials
3. Testing connection
4. Saving to .env file
"""
import os
import sys
from getpass import getpass


def print_banner():
    print("\n" + "=" * 70)
    print("   📧 RenewAI Email Service Setup Wizard")
    print("=" * 70 + "\n")


def print_gmail_instructions():
    print("\n📝 Gmail Setup Instructions:")
    print("-" * 70)
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if not already enabled)")
    print("3. Go to: https://myaccount.google.com/apppasswords")
    print("4. Select 'Mail' and 'Other (Custom name)'")
    print("5. Name it 'RenewAI' and click 'Generate'")
    print("6. Copy the 16-character password (e.g., 'abcd efgh ijkl mnop')")
    print("7. Paste it below (spaces will be removed automatically)")
    print("-" * 70)


def print_outlook_instructions():
    print("\n📝 Outlook/Office365 Setup Instructions:")
    print("-" * 70)
    print("1. Go to: https://account.microsoft.com/security")
    print("2. Enable 2-Step Verification")
    print("3. Create an App Password for 'Mail'")
    print("4. Copy the generated password")
    print("5. Paste it below")
    print("-" * 70)


def choose_provider():
    print("Which email provider do you want to use?\n")
    print("1. Gmail (most common)")
    print("2. Outlook / Office365")
    print("3. Custom SMTP server")
    print("4. Skip (use stub mode for now)\n")
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice == '1':
            return 'gmail'
        elif choice == '2':
            return 'outlook'
        elif choice == '3':
            return 'custom'
        elif choice == '4':
            return 'skip'
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


def get_credentials(provider):
    if provider == 'skip':
        return None
    
    if provider == 'gmail':
        print_gmail_instructions()
    elif provider == 'outlook':
        print_outlook_instructions()
    
    print(f"\n🔑 Enter your {provider.upper()} credentials:\n")
    
    username = input("Email address: ").strip()
    password = getpass("App password (hidden): ").strip()
    password = password.replace(' ', '')  # Remove spaces from Gmail app passwords
    
    from_name = input("Sender name (default: Suraksha Life Insurance): ").strip()
    if not from_name:
        from_name = "Suraksha Life Insurance"
    
    if provider == 'custom':
        smtp_host = input("SMTP host (e.g., smtp.example.com): ").strip()
        smtp_port = input("SMTP port (default: 587): ").strip() or '587'
    else:
        smtp_host = None
        smtp_port = None
    
    return {
        'provider': provider,
        'username': username,
        'password': password,
        'from_name': from_name,
        'smtp_host': smtp_host,
        'smtp_port': smtp_port
    }


def test_connection(credentials):
    print("\n🧪 Testing SMTP connection...\n")
    
    # Set environment variables temporarily
    os.environ['SMTP_PROVIDER'] = credentials['provider']
    os.environ['SMTP_USERNAME'] = credentials['username']
    os.environ['SMTP_PASSWORD'] = credentials['password']
    os.environ['SMTP_FROM_NAME'] = credentials['from_name']
    
    if credentials.get('smtp_host'):
        os.environ['SMTP_HOST'] = credentials['smtp_host']
        os.environ['SMTP_PORT'] = credentials['smtp_port']
    
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        result = email_service.test_connection()
        
        if result['success']:
            print("✅ SUCCESS! Connection established.")
            print(f"   Provider: {result['provider']}")
            print(f"   Host: {result['host']}:{result['port']}")
            print(f"   Username: {result['username']}")
            return True
        else:
            print("❌ FAILED! Connection could not be established.")
            print(f"   Error: {result.get('message')}")
            if 'help' in result:
                print(f"   Help: {result['help']}")
            return False
    
    except Exception as e:
        print(f"❌ FAILED! Error: {e}")
        return False


def save_to_env(credentials):
    print("\n💾 Saving configuration to .env file...\n")
    
    env_path = '/home/labuser/Desktop/SUREKHA_INSURANCE/.env'
    
    # Read existing .env
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Remove old SMTP config
    env_lines = [line for line in env_lines if not line.startswith('SMTP_')]
    
    # Add new SMTP config
    env_lines.append(f"\n# SMTP Email Configuration (added by setup_email.py)\n")
    env_lines.append(f"SMTP_PROVIDER={credentials['provider']}\n")
    env_lines.append(f"SMTP_USERNAME={credentials['username']}\n")
    env_lines.append(f"SMTP_PASSWORD={credentials['password']}\n")
    env_lines.append(f"SMTP_FROM_NAME={credentials['from_name']}\n")
    
    if credentials.get('smtp_host'):
        env_lines.append(f"SMTP_HOST={credentials['smtp_host']}\n")
        env_lines.append(f"SMTP_PORT={credentials['smtp_port']}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(env_lines)
    
    print(f"✅ Configuration saved to {env_path}")
    print("\n🎉 Email service is now configured!")


def send_test_email():
    print("\n📧 Would you like to send a test email? (y/n): ", end='')
    choice = input().strip().lower()
    
    if choice != 'y':
        print("Skipping test email.")
        return
    
    test_email = input("\nEnter recipient email address: ").strip()
    
    print(f"\n📤 Sending test email to {test_email}...\n")
    
    try:
        from services.email_service import get_email_service
        email_service = get_email_service()
        
        result = email_service.send_renewal_email(
            customer_name="Test Customer",
            customer_email=test_email,
            policy_number="TEST-001",
            policy_type="Term Life Insurance",
            premium_amount=25000,
            due_date="31 March 2026",
            sum_assured=5000000,
            offers=[
                "10% No-Claim Discount - Save ₹2,500",
                "₹500 AutoPay Cashback",
                "Premium Holiday - Skip 1 month after renewal"
            ],
            payment_link="https://pay.suraksha.in/test-001",
            language="en"
        )
        
        if result['success']:
            print("✅ Test email sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Check your inbox at: {test_email}")
        else:
            print("❌ Failed to send test email")
            print(f"   Error: {result.get('message')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print_banner()
    
    provider = choose_provider()
    
    if provider == 'skip':
        print("\n⏭️  Skipping email configuration.")
        print("Email agent will run in STUB mode (logs only, no actual sending).")
        print("You can run this script again later to configure.\n")
        return
    
    credentials = get_credentials(provider)
    
    if test_connection(credentials):
        save_to_env(credentials)
        send_test_email()
        
        print("\n" + "=" * 70)
        print("   ✅ Setup Complete!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Restart your FastAPI server: pkill -f uvicorn && python -m uvicorn api.main:app --reload")
        print("2. Restart Streamlit: pkill -f streamlit && streamlit run dashboard.py")
        print("3. Go to Dashboard → Run Journeys → Click 'Run Journey A'")
        print("4. Check the email inbox you configured!")
        print("\n🎉 Your Email Agent is now LIVE and sending real emails!\n")
    else:
        print("\n❌ Setup failed. Please check your credentials and try again.")
        print("Run: python3 setup_email.py\n")


if __name__ == '__main__':
    main()
