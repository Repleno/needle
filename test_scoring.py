"""
Thin shim — full test suite lives in tests/test_scoring.py.
Run all tests with: python3 tests/test_scoring.py
"""
from datetime import datetime, timezone, timedelta
from reddit_scout import detect_astroturfing_penalty


def test_astroturfing_penalty_applied():
    """Verify penalty applied when all astroturfing conditions are met."""
    post = {
        "title": "How I solved my problems",
        "selftext": (
            "I used to struggle. Then I found SuperApp. "
            "The tracking and automation features are great. "
            "The dashboard is nice. It was a game changer for me."
        ),
        "author_created_utc": (
            datetime.now(timezone.utc) - timedelta(days=100)
        ).timestamp()
    }
    penalty = detect_astroturfing_penalty(post)
    assert penalty == -5


def test_astroturfing_penalty_not_applied_genuine():
    """Verify no penalty for genuine posts."""
    post = {
        "title": "Need help with inventory",
        "selftext": (
            "I ran out of stock. It is a game changer if I can fix this. "
            "Any recommendations?"
        ),
        "author_created_utc": (
            datetime.now(timezone.utc) - timedelta(days=100)
        ).timestamp()
    }
    penalty = detect_astroturfing_penalty(post)
    assert penalty == 0


def test_young_account_penalty():
    """Verify young accounts receive a penalty."""
    post = {
        "title": "Just asking a question",
        "selftext": "Nothing special here.",
        "author_created_utc": (
            datetime.now(timezone.utc) - timedelta(days=10)
        ).timestamp()
    }
    penalty = detect_astroturfing_penalty(post)
    assert penalty == -2
