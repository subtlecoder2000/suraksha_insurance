"""
services/rag_retrieval.py
RAG Retrieval Engine — Layer 2 AI Platform Services
Retrieves relevant policy documents, objection responses, and fund NAVs.
Uses simple keyword scoring (production: replace with vector embeddings).
"""
from __future__ import annotations
from data.policy_store import get_policy_summary, get_all_navs, get_product
from data.objection_library import search_objection, format_response


def retrieve_policy_context(product_code: str) -> str:
    """Fetch policy summary for grounding LLM responses."""
    return get_policy_summary(product_code)


def retrieve_objection_response(
    objection_text: str,
    language: str = "English",
    segment: str = None,
    context: dict = None,
) -> str:
    """
    Retrieve the best matching objection response from the RAG library.
    Fills in policy-specific placeholders from context.
    """
    results = search_objection(objection_text, language=language, segment=segment, top_k=1)
    if not results:
        return (
            "I completely understand your concern. Let me connect you with a specialist "
            "who can give you personalised guidance. Shall I transfer you?"
        )
    best = results[0]
    return format_response(best, context or {})


def retrieve_fund_nav_context() -> str:
    """Return formatted fund NAV table for ULIP policy holders."""
    navs = get_all_navs()
    rows = [f"  • {n.fund_name} ({n.category}): NAV ₹{n.nav} as of {n.date}" for n in navs]
    return "Current Fund NAVs:\n" + "\n".join(rows)


def build_rag_context(policy_id: str, product_code: str, objection: str = None,
                      language: str = "English", segment: str = None,
                      policyholder_context: dict = None) -> dict:
    """
    Build a complete RAG context bundle for the LLM.
    Returns a dict with policy_summary, objection_response, fund_navs.
    """
    context = {}
    context["policy_summary"] = retrieve_policy_context(product_code)

    if objection:
        context["objection_response"] = retrieve_objection_response(
            objection, language=language, segment=segment, context=policyholder_context
        )

    product = get_product(product_code)
    if product and product.policy_type == "ULIP":
        context["fund_navs"] = retrieve_fund_nav_context()

    return context
