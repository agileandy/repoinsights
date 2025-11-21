#!/usr/bin/env python3
"""
Demo script to show the GitHub Network Insight Analyzer functionality
without requiring a real GitHub token.
"""

import sys
import os

# Mock responses for demonstration
MOCK_USER_DATA = {"login": "demo-user", "name": "Demo User"}
MOCK_REPOS = [
    {"name": "repo1", "full_name": "demo-user/repo1"},
    {"name": "repo2", "full_name": "demo-user/repo2"}
]
MOCK_FOLLOWERS = [
    {"login": "follower1"},
    {"login": "follower2"},
    {"login": "follower3"}
]
MOCK_STARRED = [
    {
        "full_name": "popular/repo",
        "description": "A popular repository",
        "stargazers_count": 10000,
        "html_url": "https://github.com/popular/repo"
    },
    {
        "full_name": "hidden/gem",
        "description": "A hidden gem repository",
        "stargazers_count": 500,
        "html_url": "https://github.com/hidden/gem"
    }
]
MOCK_FOLLOWING = [
    {"login": "influential1"},
    {"login": "influential2"}
]

print("GitHub Network Insight Analyzer - Demo Mode")
print("=" * 60)
print()
print("This demo shows the expected workflow:")
print()
print("1. ✓ Verify user exists")
print("2. ✓ Fetch user's repositories")
print("3. ✓ Collect followers")
print("4. ✓ Collect stargazers from repos")
print("5. ✓ Build unique audience list")
print("6. ✓ Analyze starred repositories for each audience member")
print("7. ✓ Analyze followed users for each audience member")
print("8. ✓ Aggregate and rank results")
print("9. ✓ Filter hidden gems")
print("10. ✓ Display formatted report")
print()
print("=" * 60)
print()
print("Example Report Output:")
print()
print("📊 Top Commonly Starred Repositories")
print("1. popular/repo - Network: 3, Global: 10,000 - A popular repository")
print("2. hidden/gem - Network: 2, Global: 500 - A hidden gem repository")
print()
print("💎 Hidden Gems (< 5,000 global stars)")
print("1. hidden/gem - Network: 2, Global: 500 - A hidden gem repository")
print()
print("👥 Thought Leaders")
print("1. influential1 - Followed by 2 network members")
print("2. influential2 - Followed by 2 network members")
print()
print("=" * 60)
print()
print("To run with real data, set GITHUB_TOKEN and run:")
print("  python insights.py <username>")
print()
print("Key Features:")
print("  ✓ API rate limiting with automatic retry")
print("  ✓ Error handling for missing/private users")
print("  ✓ Configurable network size limits")
print("  ✓ Both text and JSON output formats")
print("  ✓ Progress indicators during analysis")
print("  ✓ Filters out target user's own repositories")
print()
