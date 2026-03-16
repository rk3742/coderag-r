"""
Confidence scorer for CodeRAG-R.
Before generating an answer, checks if retrieved chunks are
relevant enough to answer the question reliably.
Prevents hallucination by refusing to answer when evidence is weak.
"""
from typing import List, Dict, Tuple

# Thresholds tuned empirically
HIGH_CONFIDENCE   = 0.55   # answer confidently
MEDIUM_CONFIDENCE = 0.35   # answer with caveat
LOW_CONFIDENCE    = 0.20   # partial answer, warn strongly
NO_CONFIDENCE     = 0.10   # refuse to answer


def compute_confidence(chunks: List[Dict], question: str) -> Tuple[float, str, str]:
    """
    Compute a confidence score for the retrieved chunks.

    Returns:
        score      : float 0-1
        level      : "high" | "medium" | "low" | "none"
        message    : human-readable explanation
    """
    if not chunks:
        return 0.0, "none", "No relevant code found in the codebase for this question."

    scores = [c.get("relevance_score", 0.0) for c in chunks]
    top_score   = max(scores)
    avg_score   = sum(scores) / len(scores)
    top3_avg    = sum(sorted(scores, reverse=True)[:3]) / min(3, len(scores))

    # Weight: top score matters most (40%), top-3 average (40%), overall avg (20%)
    composite = (top_score * 0.40) + (top3_avg * 0.40) + (avg_score * 0.20)

    # Boost if multiple retrieval methods agreed (vector + graph both found it)
    methods = set(c.get("retrieval_method", "") for c in chunks)
    if len(methods) > 1:
        composite = min(1.0, composite * 1.15)

    # Determine level
    if composite >= HIGH_CONFIDENCE:
        level   = "high"
        message = ""
    elif composite >= MEDIUM_CONFIDENCE:
        level   = "medium"
        message = (
            "⚠️ Moderate confidence — the retrieved code is related but may not fully answer your question. "
            "Consider checking the cited files directly for complete context."
        )
    elif composite >= LOW_CONFIDENCE:
        level   = "low"
        message = (
            "⚠️ Low confidence — I found some loosely related code but I'm not certain it answers your question. "
            "The answer below is my best attempt but verify it manually."
        )
    else:
        level   = "none"
        message = (
            "❌ I couldn't find reliable information about this in the codebase. "
            "The question may be about functionality that doesn't exist, uses different terminology, "
            "or is in files not yet indexed. Try rephrasing or check if the relevant files are included."
        )

    return round(composite, 3), level, message


def build_confidence_prefix(level: str, message: str, chunks: List[Dict]) -> str:
    """
    Build a prefix to inject into the LLM system prompt
    based on confidence level.
    """
    if level == "high":
        return (
            "You have HIGH confidence in the retrieved context. "
            "Answer directly and cite specific file/function/line references."
        )
    elif level == "medium":
        return (
            "You have MEDIUM confidence in the retrieved context. "
            "Answer based on what you found but clearly note any gaps or assumptions. "
            "Do not invent code that isn't shown."
        )
    elif level == "low":
        return (
            "You have LOW confidence in the retrieved context. "
            "Be honest that the evidence is weak. "
            "Share what you found but explicitly say you are not certain this is correct. "
            "Suggest the user verify manually."
        )
    else:
        return (
            "You have NO relevant context for this question. "
            "Do NOT make up an answer. "
            "Tell the user clearly that you couldn't find this in the codebase "
            "and suggest what they might search for instead."
        )
