"""
config/settings.py
Central configuration and constants for PROJECT RenewAI v2.0
Based on: Suraksha Life Insurance Business Case — RenewAI (June 2025)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Company Identity ───────────────────────────────────────────────────────────
COMPANY_NAME = "Suraksha Life Insurance"
COMPANY_EST  = 2003
COMPANY_HQ   = "Mumbai, India"
IRDAI_SOLVENCY_RATIO = 2.1      # vs 1.5x mandated

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")   # stub | openai | azure
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# ── Voice ─────────────────────────────────────────────────────────────────────
VOICE_STUB = os.getenv("VOICE_STUB", "true").lower() == "true"
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "centralindia")   # India region

# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_REGENERATE_LOOPS = int(os.getenv("MAX_REGENERATE_LOOPS", 3))
CRITIQUE_COST_PER_MSG_INR = float(os.getenv("CRITIQUE_COST_PER_MSG_INR", 0.035))

# ── Compliance ────────────────────────────────────────────────────────────────
IRDAI_FRAMEWORK_YEAR = 2024
RBI_FREE_AI_FRAMEWORK = 2025
DPDPA_YEAR = 2023
DATA_RESIDENCY = "India"   # No data leaves India

# ── Business Metrics (FY25 Baseline from Business Case) ───────────────────────
TOTAL_POLICYHOLDERS   = 4_800_000
ANNUAL_PREMIUM_INCOME_CR = 3240          # ₹ Crore
RENEWAL_PREMIUM_CR    = 1890             # ₹ Crore (58% of total)
ANNUAL_RENEWAL_COUNT  = 1_440_000        # ~14.4 lakh policies due/yr
AVG_POLICY_PREMIUM    = 22_400           # ₹ per policy per year
ANNUAL_LAPSE_RATE_PCT = 29               # %
CURRENT_PERSISTENCY_13M = 0.71          # 71%
TARGET_PERSISTENCY_13M  = 0.88          # 88%
CURRENT_PERSISTENCY_61M = 0.42          # 42%
CURRENT_TEAM_SIZE     = 120
TARGET_TEAM_SIZE      = 20
CURRENT_ANNUAL_OPEX_CR = 18.6           # ₹ Crore
TARGET_ANNUAL_OPEX_CR  = 5.7            # ₹ Crore
ANNUAL_SAVING_CR       = 12.9           # ₹ Crore
INCREMENTAL_REVENUE_CR = 38.9           # Net revenue uplift
NPV_3YR_CR             = 89             # 3-year NPV
PAYBACK_MONTHS         = 8

# ── Renewal Journey Triggers (T-minus days) ────────────────────────────────────
# Replaces the old 30-15-7 rigid schedule
RENEWAL_JOURNEY = {
    "T45": {"channel": "email",             "action": "personalized_renewal_reminder"},
    "T30": {"channel": "whatsapp",          "action": "conversational_message_with_payment_link"},
    "T20": {"channel": "voice",             "action": "outbound_ai_call"},
    "T10": {"channel": "whatsapp+email",    "action": "last_chance_with_ecs_autopay"},
    "T5":  {"channel": "voice+whatsapp",    "action": "urgent_dual_channel_with_grace_period"},
    "POST_LAPSE": {"channel": "multi",      "action": "90_day_revival_campaign"},
}

# ── AI System Targets ─────────────────────────────────────────────────────────
HUMAN_ESCALATION_RATE_TARGET = 0.10   # ≤10%
AI_ACCURACY_TARGET = 0.87             # ≥87%
EMAIL_OPEN_RATE_TARGET = 0.42         # 42%
WA_RESPONSE_RATE_TARGET = 0.58        # 58%
VOICE_CONVERSION_TARGET = 0.31        # 31% (calls → payment within 48h)
NPS_BASELINE = 34
NPS_TARGET   = 55
COST_PER_RENEWAL_BASELINE = 182       # ₹
COST_PER_RENEWAL_TARGET   = 45        # ₹
DISTRESS_ESCALATION_SLA_HRS = 2       # All distress cases escalated within 2 hours
QUALITY_EVAL_SAMPLE_PCT = 0.05        # 5% random weekly sample

# ── Loyalty & Offers ──────────────────────────────────────────────────────────
NO_CLAIM_DISCOUNT_TIERS = {0: 0.05, 3: 0.10, 5: 0.15}
AUTOPAY_CASHBACK_INR = 200
EARLY_RENEWAL_REMINDER_DAYS = 60
GRACE_PERIOD_DAYS = 30
REVIVAL_WINDOW_DAYS = 90
PREMIUM_HOLIDAY_MONTHS = 1

# ── Critique Agent ─────────────────────────────────────────────────────────────
CRITIQUE_PASS_THRESHOLD = 0.87
CRITIQUE_BLOCK_KEYWORDS = [
    "guaranteed returns", "100% safe", "no risk", "assured profit",
    "SEBI approved", "government backed", "risk-free investment",
    "beats mutual fund guaranteed", "fixed market returns"
]

# ── Channels ──────────────────────────────────────────────────────────────────
SUPPORTED_CHANNELS = ["email", "whatsapp", "voice"]
SUPPORTED_LANGUAGES = [
    "Hindi", "English", "Tamil", "Telugu", "Bengali",
    "Marathi", "Kannada", "Malayalam", "Gujarati"
]

# ── Customer Segments ─────────────────────────────────────────────────────────
CUSTOMER_SEGMENTS = ["Wealth Builder", "Budget Conscious", "Young Professional", "Senior Citizen"]

# ── Product Portfolio (38 plans — key types) ──────────────────────────────────
POLICY_TYPES = ["Term", "Endowment", "ULIP", "Pension", "Health"]

# ── Distribution Network ──────────────────────────────────────────────────────
AGENT_NETWORK = 87_000
BRANCHES = 420
BANCASSURANCE_PARTNERS = 14

# ── Persistency Uplift Economics ──────────────────────────────────────────────
# Every 1% improvement in persistency → ₹4.7 Cr additional premium income
PERSISTENCY_UPLIFT_PER_PCT_CR = 4.7

# ── Tech Stack (Azure India Cloud) ────────────────────────────────────────────
CLOUD_PROVIDER = "Azure"
CLOUD_REGION   = "Central India"   # Data residency
ISO_27001 = True
SOC2_TYPE2 = True

# ── Distress Keywords (Hindi + English + Regional) ────────────────────────────
DISTRESS_KEYWORDS_EN = [
    "passed away", "death", "bereavement", "husband died", "wife died",
    "bankrupt", "lost job", "no money", "can't afford", "financial hardship",
    "suicidal", "depressed", "hopeless", "illness", "critical condition",
    "fraud", "cheated", "consumer forum", "legal action", "ombudsman",
]
DISTRESS_KEYWORDS_HI = [
    "guzar gaye", "mrityu", "naukri gayi", "paisa nahi", "takleef",
    "pareshan", "berozgar", "bimar", "hospital",
]
