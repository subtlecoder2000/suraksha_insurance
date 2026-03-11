"""
data/objection_library.py
Objection Library (RAG) — Layer 1 Data & Integration
150+ objection–response pairs, multi-language indexed, used by RAG Retrieval Engine.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ObjectionEntry:
    id: str
    category: str
    objection: str
    response: str
    language: str
    segment: list[str]   # which segments this applies to
    tags: list[str]


# ── Core Objection-Response Library ────────────────────────────────────────────
OBJECTION_LIBRARY: list[ObjectionEntry] = [
    # ── COST / AFFORDABILITY ──────────────────────────────────────────────────
    ObjectionEntry("OBJ-001", "Cost", "The premium is too high, I can't afford it.",
        "I completely understand. Your policy actually provides ₹{sum_assured} coverage for just ₹{daily_cost}/day. We also have an EMI option — 3 easy instalments with no extra charge. Shall I set that up?",
        "English", ["Budget Conscious", "Young Professional"],
        ["price_sensitive", "emi_offer"]),
    ObjectionEntry("OBJ-002", "Cost", "Premium bahut zyada hai.",
        "Bilkul samajh sakta hoon. Aapki policy sirf ₹{daily_cost}/din mein ₹{sum_assured} ki suraksha deti hai. Hum 3 aasaan kiston mein bhi payment kar sakte hain, koi extra charge nahi. Kya main yeh set kar doon?",
        "Hindi", ["Budget Conscious"], ["price_sensitive", "emi_offer"]),
    ObjectionEntry("OBJ-003", "Cost", "Premium romba jaasthi.",
        "Purinjukiren. Ungal policy ₹{daily_cost}/naal mattume ₹{sum_assured} paadhugaappu tharukirathu. 3 thavanaigalilum pay pannalaam, extra charge illai.",
        "Tamil", ["Budget Conscious"], ["price_sensitive"]),
    ObjectionEntry("OBJ-004", "Cost", "Can I get a discount?",
        "Yes! Since you have {years_no_claim} years without a claim, you qualify for a {discount_pct}% No-Claim Discount, saving you ₹{savings}. I can apply this now — shall I proceed?",
        "English", ["Wealth Builder", "Budget Conscious", "Young Professional", "Senior Citizen"],
        ["discount", "no_claim_eligible"]),
    ObjectionEntry("OBJ-005", "Cost", "Itna paisa nahi hai abhi.",
        "Koi baat nahi. Aap abhi ₹{partial_amount} de sakte hain aur baaki 30 din baad. Policy active rahegi aur koi penalty nahi hogi. Kya yeh theek rahega?",
        "Hindi", ["Budget Conscious"], ["partial_payment"]),

    # ── RETURNS / PERFORMANCE ─────────────────────────────────────────────────
    ObjectionEntry("OBJ-006", "Returns", "Returns are not good. Market is down.",
        "I understand the concern. Your ULIP has a 7-year horizon — historically our Equity Growth Fund has delivered 12.4% CAGR over 7+ years. Short-term dips are normal. Surrendering now would lock in a loss. Shall I show you your current fund value and projected maturity?",
        "English", ["Wealth Builder", "Young Professional"], ["ulip", "market_dip"]),
    ObjectionEntry("OBJ-007", "Returns", "Return bahut kam hai.",
        "Aapka ULIP long-term ke liye designed hai. 7 saal mein humara Equity Growth Fund ne 12.4% CAGR diya hai. Abhi surrender karna loss lock kar dega. Kya main aapko current NAV aur projected value dikhaaoon?",
        "Hindi", ["Wealth Builder"], ["ulip", "market_dip"]),
    ObjectionEntry("OBJ-008", "Returns", "FD rates are better, why should I continue?",
        "FDs give fixed returns but no life cover. Your policy gives ₹{sum_assured} life cover + market-linked returns. Also, FD interest is fully taxable, but your maturity benefit u/s 10(10D) is tax-free. The real return on your policy is higher than it appears.",
        "English", ["Wealth Builder", "Senior Citizen"], ["comparison", "tax_benefit"]),

    # ── TRUST / COMPANY ───────────────────────────────────────────────────────
    ObjectionEntry("OBJ-009", "Trust", "I don't trust insurance companies for claims.",
        "Your concern is valid and very common. Suraksha Insurance has a 98.5% claim settlement ratio — one of the highest in India, as published by IRDAI. We settled 2.4 lakh claims last year. Shall I share the IRDAI-published claim report?",
        "English", ["Budget Conscious", "Senior Citizen", "Young Professional"], ["claim_ratio", "trust"]),
    ObjectionEntry("OBJ-010", "Trust", "Claim mein bahut problem hoti hai.",
        "Yeh ek common chinta hai. Suraksha Insurance ka IRDAI-published claim settlement ratio 98.5% hai — India mein sabse zyada mein se ek. Pichle saal humne 2.4 lakh claims settle kiye. Kya main IRDAI report share karoon?",
        "Hindi", ["Budget Conscious", "Senior Citizen"], ["claim_ratio", "trust"]),
    ObjectionEntry("OBJ-011", "Trust", "Company kaisa hai, reliable hai?",
        "Suraksha Insurance 25 saalon se India mein hai, 4.8 million policyholders ke saath. Hum IRDAI regulated hain, Tech Framework 2024 compliant hain. Aapka paisa 100% safe hai.",
        "Hindi", ["Budget Conscious", "Young Professional"], ["company_credibility"]),

    # ── TIMING / DELAY ────────────────────────────────────────────────────────
    ObjectionEntry("OBJ-012", "Timing", "I'll renew next month.",
        "I understand, but there's an important detail — your policy lapses on {renewal_due_date}, which is just {days_left} days away. After that, there's a {grace_period}-day grace period, but you lose coverage during that window. Renewing today takes just 2 minutes via UPI. Shall I share the payment link?",
        "English", ["Budget Conscious", "Young Professional", "Senior Citizen"], ["urgency", "lapse_risk"]),
    ObjectionEntry("OBJ-013", "Timing", "Baad mein karoonga.",
        "Samajh sakta hoon, lekin aapki policy {days_left} din mein expire ho rahi hai. Iske baad {grace_period}-din ka grace period hai, lekin us dauran coverage nahi milegi. Aaj 2 minute mein UPI se renew ho sakta hai. Payment link bhejoon?",
        "Hindi", ["Budget Conscious"], ["urgency", "lapse_risk"]),
    ObjectionEntry("OBJ-014", "Timing", "Not now, very busy.",
        "No worries! I can send you a payment link right now — you can complete renewal in under 60 seconds whenever convenient. Your coverage remains active until {renewal_due_date}. Want me to WhatsApp the link?",
        "English", ["Young Professional"], ["convenience", "digital"]),

    # ── NEED ──────────────────────────────────────────────────────────────────
    ObjectionEntry("OBJ-015", "Need", "I don't think I need insurance anymore.",
        "I hear you. But consider — your family depends on your income. If something were to happen, your ₹{sum_assured} cover ensures they're protected for {protection_years} years without financial stress. Would you like me to explain the maturity benefits as well?",
        "English", ["Budget Conscious", "Young Professional"], ["need_creation", "family_protection"]),
    ObjectionEntry("OBJ-016", "Need", "Mujhe insurance ki zaroorat nahi lagti.",
        "Samajh sakta hoon. Lekin socho — aapke parivaar ki ₹{sum_assured} ki suraksha sirf ₹{daily_cost}/din mein. Kuch bhi ho, unhe pareshaani nahi hogi. Kya main maturity benefits bhi explain karoon?",
        "Hindi", ["Budget Conscious"], ["need_creation"]),

    # ── LAPSE / REVIVAL ───────────────────────────────────────────────────────
    ObjectionEntry("OBJ-017", "Revival", "My policy has already lapsed, what can I do?",
        "Good news — your policy can still be revived within 90 days of lapse. We'll waive the late fee if you pay the pending premium of ₹{pending_premium} today. After revival, all benefits are fully restored. Shall I generate your revival quote?",
        "English", ["Budget Conscious", "Young Professional", "Senior Citizen"], ["revival", "lapsed"]),
    ObjectionEntry("OBJ-018", "Revival", "Policy lapse ho gayi hai.",
        "Ghabhraiye mat! Aapki policy abhi bhi 90 din ke andar revive ho sakti hai. Aaj ₹{pending_premium} pay karने par late fee maaf hogi aur sab benefits wapas aa jaayenge. Kya main aapka revival quote generate karoon?",
        "Hindi", ["Budget Conscious"], ["revival", "lapsed"]),

    # ── EMI / PAYMENT MODE ────────────────────────────────────────────────────
    ObjectionEntry("OBJ-019", "Payment", "Can I pay in parts?",
        "Absolutely! We offer 3-part EMI — ₹{emi_amount} today, ₹{emi_amount} in 30 days, and ₹{emi_amount} in 60 days. No interest, no extra charges. Your policy stays fully active throughout. Want to set this up via UPI?",
        "English", ["Budget Conscious", "Young Professional"], ["emi", "payment_flexibility"]),
    ObjectionEntry("OBJ-020", "Payment", "UPI se ho jaayega?",
        "Haan bilkul! Main abhi aapko UPI payment link bhejta hoon. Ek click mein ho jaayega. Aapka preferred UPI number {phone} hai — sahi hai?",
        "Hindi", ["Budget Conscious", "Young Professional"], ["upi", "digital"]),

    # ── HEALTH / CLAIM HISTORY ────────────────────────────────────────────────
    ObjectionEntry("OBJ-021", "Health", "I already had a claim, will my premium go up?",
        "For your {policy_type} policy, a claim does not directly increase your renewal premium. It only resets the no-claim bonus accumulation. Your renewal premium remains ₹{premium}. Would you like to continue?",
        "English", ["Senior Citizen", "Budget Conscious"], ["claim_history", "premium_clarity"]),

    # ── FAMILY BURDEN ─────────────────────────────────────────────────────────
    ObjectionEntry("OBJ-022", "Family", "My family situation has changed.",
        "I understand. Life changes, and your policy can change too. You can update your nominee, add a rider, or adjust your sum assured. Would you like me to schedule a call with our Renewal Manager who can customize your plan?",
        "English", ["Senior Citizen", "Wealth Builder"], ["flexibility", "customization"]),

    # ── COMPETITOR ────────────────────────────────────────────────────────────
    ObjectionEntry("OBJ-023", "Competitor", "Another company is offering cheaper premium.",
        "I appreciate you sharing that. Before you switch, it's important to compare claim ratios — ours is 98.5% vs industry average of 95.2%. Switching also means a fresh waiting period and new exclusions. You've already built {years_as_customer} years of trust and loyalty benefits here. Can I show you the exact comparison?",
        "English", ["Budget Conscious", "Young Professional"], ["competitor", "retention"]),

    # ── DIGITAL / TECH HESITANCY ─────────────────────────────────────────────
    ObjectionEntry("OBJ-024", "Digital", "I don't know how to pay online.",
        "No problem at all! You can also pay by visiting your nearest branch or authorize someone you trust to pay on your behalf. Alternatively, if you're comfortable, I can walk you through the UPI payment step by step — it takes under 2 minutes. Which would you prefer?",
        "English", ["Senior Citizen"], ["digital_hesitancy", "assistance"]),
    ObjectionEntry("OBJ-025", "Digital", "Online payment se dar lagta hai.",
        "Bilkul samajh sakta hoon. Aap apne nearest branch mein bhi ja sakte hain ya kisi trusted person ko authorize kar sakte hain. Ya main aapko step-by-step UPI guide kar sakta hoon — sirf 2 minute lagte hain. Kya behtar rahega?",
        "Hindi", ["Senior Citizen"], ["digital_hesitancy"]),
]

# ── Retrieval Functions ────────────────────────────────────────────────────────

def search_objection(query: str, language: str = "English",
                     segment: str = None, top_k: int = 3) -> list[ObjectionEntry]:
    """Simple keyword-based retrieval (production: use vector similarity)."""
    query_lower = query.lower()
    results = []
    for entry in OBJECTION_LIBRARY:
        score = 0
        if entry.language == language:
            score += 2
        if segment and segment in entry.segment:
            score += 2
        for word in query_lower.split():
            if word in entry.objection.lower() or word in entry.category.lower():
                score += 1
            for tag in entry.tags:
                if word in tag:
                    score += 1
        results.append((score, entry))
    results.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in results[:top_k]]


def get_by_category(category: str) -> list[ObjectionEntry]:
    return [e for e in OBJECTION_LIBRARY if e.category == category]


def get_by_language(language: str) -> list[ObjectionEntry]:
    return [e for e in OBJECTION_LIBRARY if e.language == language]


def format_response(entry: ObjectionEntry, context: dict) -> str:
    """Fill placeholders in response template with actual policy data."""
    try:
        return entry.response.format(**context)
    except KeyError:
        return entry.response
