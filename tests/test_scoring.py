#!/usr/bin/env python3
"""
Tests for needle scoring and filtering logic.

Run with: python3 tests/test_scoring.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports (must be before local imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest  # pylint: disable=wrong-import-position
from datetime import datetime, timezone  # pylint: disable=wrong-import-position

# pylint: disable=wrong-import-position
from reddit_scout import (
    score_post,
    is_recent,
    detect_astroturfing_penalty,
    filter_and_score,
    format_email_html,
    validate_config,
    RELEVANCE_KEYWORDS,
    SKIP_PATTERNS,
)


class TestSkipPatterns(unittest.TestCase):
    """Tests for SKIP_PATTERNS filtering."""

    def test_hiring_post_skipped(self):
        """Verify hiring posts are skipped."""
        post = {
            "title": "[hiring] looking for developers",
            "selftext": "",
            "subreddit": "test"
        }
        self.assertEqual(score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS), -1)

    def test_job_post_skipped(self):
        """Verify job posts are skipped."""
        post = {
            "title": "[job] python developer needed",
            "selftext": "",
            "subreddit": "test"
        }
        self.assertEqual(score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS), -1)

    def test_self_promo_skipped(self):
        """Verify self-promo posts are skipped."""
        post = {
            "title": "I made this inventory tool",
            "selftext": "",
            "subreddit": "test"
        }
        self.assertEqual(score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS), -1)

    def test_for_sale_skipped(self):
        """Verify for-sale posts are skipped."""
        post = {
            "title": "For sale: warehouse equipment",
            "selftext": "",
            "subreddit": "test"
        }
        self.assertEqual(score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS), -1)

    def test_normal_post_not_skipped(self):
        """Verify normal posts are not skipped."""
        post = {
            "title": "Help with inventory management",
            "selftext": "",
            "subreddit": "test"
        }
        self.assertGreaterEqual(
            score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS), 0
        )


class TestKeywordScoring(unittest.TestCase):
    """Tests for keyword matching and scoring."""

    def test_strong_signal_scores_high(self):
        """Verify strong signals get high scores."""
        post = {
            "title": "We ran out of stock again",
            "selftext": "",
            "subreddit": "test"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertGreaterEqual(score, 6)  # "ran out" (3) + "stock" (3)

    def test_score_capped_at_20(self):
        """Verify score is capped at 20."""
        post = {
            "title": "inventory stock reorder replenish out of stock ran out",
            "selftext": "material supplies excel spreadsheet manual tracking",
            "subreddit": "warehouse"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertLessEqual(score, 20)

    def test_word_boundary_stockbroker(self):
        """Ensure 'stock' doesn't match 'stockbroker'."""
        post = {
            "title": "My friend is a stockbroker",
            "selftext": "",
            "subreddit": "finance"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertEqual(score, 0)

    def test_word_boundary_woodstock(self):
        """Ensure 'stock' doesn't match 'Woodstock'."""
        post = {
            "title": "Going to Woodstock festival",
            "selftext": "",
            "subreddit": "music"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertEqual(score, 0)

    def test_word_boundary_backtracking(self):
        """Ensure 'tracking' doesn't match 'backtracking'."""
        post = {
            "title": "Backtracking algorithm explained",
            "selftext": "",
            "subreddit": "programming"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertEqual(score, 0)


class TestIsRecent(unittest.TestCase):
    """Tests for time-based filtering."""

    def test_recent_post_passes(self):
        """Verify recent posts pass the filter."""
        now = datetime.now(timezone.utc).timestamp()
        post = {"created_utc": now - 3600}  # 1 hour ago
        self.assertTrue(is_recent(post, recent_hours=24))

    def test_old_post_filtered(self):
        """Verify old posts are filtered out."""
        now = datetime.now(timezone.utc).timestamp()
        post = {"created_utc": now - 86400 * 2}  # 2 days ago
        self.assertFalse(is_recent(post, recent_hours=24))

    def test_edge_case_just_under_24h(self):
        """Verify posts just under 24h pass."""
        now = datetime.now(timezone.utc).timestamp()
        post = {"created_utc": now - 86400 + 60}  # 24h minus 1 minute
        self.assertTrue(is_recent(post, recent_hours=24))

    def test_missing_timestamp(self):
        """Verify posts without timestamp are filtered."""
        post = {}
        self.assertFalse(is_recent(post, recent_hours=24))


class TestAstroturfingDetection(unittest.TestCase):
    """Tests for astroturfing penalty."""

    def test_genuine_question_no_penalty(self):
        """Verify genuine questions get no penalty."""
        post = {
            "title": "What inventory tool do you use?",
            "selftext": (
                "We're frustrated with our current Excel setup "
                "and looking for alternatives."
            ),
        }
        penalty = detect_astroturfing_penalty(post)
        self.assertEqual(penalty, 0)  # Has dissatisfaction phrase, no penalty

    def test_obvious_ad_gets_penalty(self):
        """Verify obvious ads get penalized."""
        post = {
            "title": "InventoryPro changed our business",
            "selftext": (
                "We switched to InventoryPro and it has tracking, dashboard, analytics, "
                "and automation. Game changer for our warehouse! "
                "Highly recommend."
            ),
        }
        penalty = detect_astroturfing_penalty(post)
        self.assertLessEqual(penalty, -5)  # Should get astroturfing penalty

    def test_young_account_penalty(self):
        """Verify young accounts get penalized."""
        now = datetime.now(timezone.utc).timestamp()
        post = {
            "title": "What tool do you use?",
            "selftext": "",
            "author_created_utc": now - 86400 * 15,  # 15 days old
        }
        penalty = detect_astroturfing_penalty(post)
        self.assertEqual(penalty, -2)  # Young account penalty


class TestEdgeCases(unittest.TestCase):
    """Edge cases and regression tests."""

    def test_empty_post(self):
        """Verify empty posts score zero."""
        post = {"title": "", "selftext": "", "subreddit": ""}
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertEqual(score, 0)

    def test_none_values(self):
        """Verify None values don't cause errors."""
        post = {"title": None, "selftext": None, "subreddit": None}
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertEqual(score, 0)

    def test_case_insensitive_matching(self):
        """Verify case-insensitive keyword matching."""
        post = {
            "title": "INVENTORY MANAGEMENT CHAOS",
            "selftext": "",
            "subreddit": "test"
        }
        score = score_post(post, RELEVANCE_KEYWORDS, SKIP_PATTERNS)
        self.assertGreaterEqual(score, 5)  # "inventory" (3) + "chaos" (2)


class TestFilterAndScore(unittest.TestCase):
    """Tests for filter_and_score integration."""

    def test_filters_seen_posts(self):
        """Verify seen posts are filtered out."""
        now = datetime.now(timezone.utc).timestamp()
        posts = [
            {
                "id": "abc", "title": "Need inventory help",
                "selftext": "", "subreddit": "test",
                "created_utc": now - 3600
            },
            {
                "id": "def", "title": "Stock tracking chaos",
                "selftext": "", "subreddit": "test",
                "created_utc": now - 3600
            },
        ]
        seen = {"abc": now}  # First post is already seen
        settings = {"score_threshold": 1, "recent_hours": 24, "max_results": 10}

        result = filter_and_score(
            posts, seen, settings, RELEVANCE_KEYWORDS, SKIP_PATTERNS
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "def")

    def test_filters_old_posts(self):
        """Verify old posts are filtered out."""
        now = datetime.now(timezone.utc).timestamp()
        posts = [
            {
                "id": "new", "title": "inventory help",
                "selftext": "", "subreddit": "test",
                "created_utc": now - 3600
            },
            {
                "id": "old", "title": "stock help",
                "selftext": "", "subreddit": "test",
                "created_utc": now - 86400 * 3
            },
        ]
        settings = {"score_threshold": 1, "recent_hours": 24, "max_results": 10}

        result = filter_and_score(
            posts, {}, settings, RELEVANCE_KEYWORDS, SKIP_PATTERNS
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "new")

    def test_respects_max_results(self):
        """Verify max_results is respected."""
        now = datetime.now(timezone.utc).timestamp()
        posts = [
            {
                "id": f"p{i}", "title": "inventory stock",
                "selftext": "", "subreddit": "test",
                "created_utc": now - 3600
            }
            for i in range(20)
        ]
        settings = {"score_threshold": 1, "recent_hours": 24, "max_results": 5}

        result = filter_and_score(
            posts, {}, settings, RELEVANCE_KEYWORDS, SKIP_PATTERNS
        )

        self.assertEqual(len(result), 5)


class TestFormatEmailHtml(unittest.TestCase):
    """Tests for email HTML generation."""

    def test_empty_posts_shows_quiet_day(self):
        """Verify empty posts show quiet day message."""
        html = format_email_html([], "2024-01-15")
        self.assertIn("Quiet day", html)
        self.assertIn("No relevant posts", html)

    def test_posts_rendered_with_scores(self):
        """Verify posts are rendered with scores."""
        now = datetime.now(timezone.utc).timestamp() - 3600
        posts = [
            {
                "_score": 15, "title": "Test Post",
                "subreddit": "test", "selftext": "Body text",
                "url": "https://reddit.com/r/test/1",
                "created_utc": now
            }
        ]
        html = format_email_html(posts, "2024-01-15")
        self.assertIn("Test Post", html)
        self.assertIn("Score 15", html)
        self.assertIn("r/test", html)

    def test_repo_url_in_footer(self):
        """Verify repo URL appears in footer."""
        html = format_email_html(
            [], "2024-01-15", repo_url="https://github.com/test/repo"
        )
        self.assertIn("https://github.com/test/repo", html)

    def test_no_repo_url_clean_footer(self):
        """Verify clean footer when no repo URL."""
        html = format_email_html([], "2024-01-15", repo_url="")
        self.assertIn("Auto-generated", html)
        footer_section = html.split("Auto-generated")[1].split("</div>")[0]
        self.assertNotIn("href=", footer_section)

    def test_html_escaping(self):
        """Verify HTML is properly escaped."""
        now = datetime.now(timezone.utc).timestamp()
        posts = [
            {
                "_score": 10,
                "title": "<script>alert('xss')</script>",
                "subreddit": "test", "selftext": "",
                "url": "#", "created_utc": now
            }
        ]
        html = format_email_html(posts, "2024-01-15")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class TestConfigValidation(unittest.TestCase):
    """Tests for config validation."""

    def test_valid_config_no_errors(self):
        """Verify valid config has no errors."""
        cfg = {
            "from_email": "test@example.com",
            "to_email": "user@example.com",
            "keyword_searches": ["test query"],
            "settings": {"score_threshold": 5}
        }
        errors = validate_config(cfg)
        self.assertEqual(len(errors), 0)

    def test_missing_email_error(self):
        """Verify missing email produces error."""
        cfg = {"keyword_searches": ["test"]}
        errors = validate_config(cfg)
        self.assertTrue(any("from_email" in e for e in errors))
        self.assertTrue(any("to_email" in e for e in errors))

    def test_invalid_score_threshold(self):
        """Verify invalid score threshold produces error."""
        cfg = {
            "from_email": "a@b.com",
            "to_email": "c@d.com",
            "keyword_searches": ["test"],
            "settings": {"score_threshold": -5}
        }
        errors = validate_config(cfg)
        self.assertTrue(any("score_threshold" in e for e in errors))

    def test_invalid_search_time(self):
        """Verify invalid search time produces error."""
        cfg = {
            "from_email": "a@b.com",
            "to_email": "c@d.com",
            "keyword_searches": ["test"],
            "settings": {"search_time": "invalid"}
        }
        errors = validate_config(cfg)
        self.assertTrue(any("search_time" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
