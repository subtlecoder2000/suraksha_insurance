"""
data/payment_gateway.py
Payment Gateway — Layer 1 Data & Integration
UPI, ECS Mandate, AutoPay, EMI/Partial Payment simulation.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class PaymentTransaction:
    txn_id: str
    policy_id: str
    amount: float
    mode: str           # UPI | ECS | AutoPay | Manual | EMI | Partial
    status: str         # Initiated | Success | Failed | Pending | Refunded
    timestamp: datetime
    utr: Optional[str] = None
    remarks: Optional[str] = None


_TRANSACTIONS: list[PaymentTransaction] = []


def initiate_payment(policy_id: str, amount: float, mode: str = "UPI") -> PaymentTransaction:
    txn = PaymentTransaction(
        txn_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
        policy_id=policy_id,
        amount=amount,
        mode=mode,
        status="Initiated",
        timestamp=datetime.now(),
    )
    _TRANSACTIONS.append(txn)
    return txn


def confirm_payment(txn_id: str, utr: Optional[str] = None) -> PaymentTransaction:
    txn = _get_txn(txn_id)
    if txn:
        txn.status = "Success"
        txn.utr = utr or f"UTR{uuid.uuid4().hex[:10].upper()}"
    return txn


def fail_payment(txn_id: str, reason: str = "Insufficient funds") -> PaymentTransaction:
    txn = _get_txn(txn_id)
    if txn:
        txn.status = "Failed"
        txn.remarks = reason
    return txn


def get_payment_history(policy_id: str) -> list[PaymentTransaction]:
    return [t for t in _TRANSACTIONS if t.policy_id == policy_id]


def generate_upi_qr(policy_id: str, amount: float) -> dict:
    return {
        "qr_code": f"upi://pay?pa=renewai@upi&pn=SurekhaInsurance&am={amount}&tn={policy_id}",
        "deeplink": f"https://pay.renewai.in/qr/{policy_id}",
        "amount": amount,
        "expires_in_minutes": 30,
    }


def setup_ecs_mandate(policy_id: str, bank_account: str, amount: float) -> dict:
    return {
        "mandate_id": f"ECS-{uuid.uuid4().hex[:8].upper()}",
        "policy_id": policy_id,
        "bank_account": bank_account[-4:].rjust(len(bank_account), "X"),
        "amount": amount,
        "status": "Registered",
        "next_debit": "On renewal date",
    }


def apply_emi_split(policy_id: str, total_amount: float, installments: int = 3) -> list[dict]:
    installment_amount = round(total_amount / installments, 2)
    return [
        {"installment": i + 1, "amount": installment_amount, "due_in_days": (i + 1) * 30}
        for i in range(installments)
    ]


def _get_txn(txn_id: str) -> Optional[PaymentTransaction]:
    return next((t for t in _TRANSACTIONS if t.txn_id == txn_id), None)
