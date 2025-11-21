#!/usr/bin/env python3
"""
Unit tests for GitHub Network Insight Analyzer
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from insights import GitHubAPIClient, NetworkAnalyzer, generate_markdown_output, is_safe_github_url, escape_markdown_table_content


class TestGitHubAPIClient(unittest.TestCase):
    """Test GitHubAPIClient class."""
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
    def test_client_initialization_with_token(self):
        """Test client initialization with token."""
        client = GitHubAPIClient()
        self.assertEqual(client.token, 'test_token')
        self.assertIsNotNone(client.session)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_client_initialization_without_token(self):
        """Test client initialization without token exits."""
        with self.assertRaises(SystemExit):
            GitHubAPIClient()
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
    @patch('insights.requests.Session')
    def test_get_request(self, mock_session):
        """Test GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000', 'X-RateLimit-Reset': '0'}
        mock_response.json.return_value = {'test': 'data'}
        
        mock_session.return_value.get.return_value = mock_response
        
        client = GitHubAPIClient()
        result = client.get('/test/endpoint')
        
        self.assertEqual(result, {'test': 'data'})
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
    @patch('insights.requests.Session')
    def test_get_request_404(self, mock_session):
        """Test GET request with 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'X-RateLimit-Remaining': '5000', 'X-RateLimit-Reset': '0'}
        
        mock_session.return_value.get.return_value = mock_response
        
        client = GitHubAPIClient()
        result = client.get('/test/endpoint')
        
        self.assertIsNone(result)


class TestNetworkAnalyzer(unittest.TestCase):
    """Test NetworkAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
            self.mock_api = Mock(spec=GitHubAPIClient)
            self.analyzer = NetworkAnalyzer(self.mock_api, limit=10, stars_per_user=5)
    
    def test_get_user_repos(self):
        """Test getting user repositories."""
        self.mock_api.get_paginated.return_value = [
            {'name': 'repo1', 'full_name': 'user/repo1'},
            {'name': 'repo2', 'full_name': 'user/repo2'}
        ]
        
        repos = self.analyzer.get_user_repos('testuser')
        
        self.assertEqual(len(repos), 2)
        self.mock_api.get_paginated.assert_called_once()
    
    def test_get_stargazers(self):
        """Test getting stargazers for a repo."""
        self.mock_api.get_paginated.return_value = [
            {'login': 'user1'},
            {'login': 'user2'},
            {'login': 'user3'}
        ]
        
        stargazers = self.analyzer.get_stargazers('owner', 'repo')
        
        self.assertEqual(len(stargazers), 3)
        self.assertIn('user1', stargazers)
    
    def test_get_followers(self):
        """Test getting followers for a user."""
        self.mock_api.get_paginated.return_value = [
            {'login': 'follower1'},
            {'login': 'follower2'}
        ]
        
        followers = self.analyzer.get_followers('testuser')
        
        self.assertEqual(len(followers), 2)
        self.assertIn('follower1', followers)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_filter_hidden_gems(self):
        """Test filtering hidden gems."""
        repo_stars = {
            'repo1': {'count': 5, 'global_stars': 100, 'description': 'A hidden gem', 'url': 'url1'},
            'repo2': {'count': 10, 'global_stars': 10000, 'description': 'Popular repo', 'url': 'url2'},
            'repo3': {'count': 3, 'global_stars': 200, 'description': 'Another gem', 'url': 'url3'},
            'repo4': {'count': 1, 'global_stars': 50, 'description': 'Too few stars', 'url': 'url4'}
        }
        
        # Mock analyzer for the method
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
            mock_api = Mock(spec=GitHubAPIClient)
            analyzer = NetworkAnalyzer(mock_api)
            gems = analyzer.filter_hidden_gems(repo_stars, threshold=5000)
        
        # Should include repos with global_stars < 5000 and count >= 2
        self.assertEqual(len(gems), 2)
        self.assertEqual(gems[0][0], 'repo1')  # Highest network stars
        self.assertEqual(gems[1][0], 'repo3')
    
    def test_generate_markdown_output(self):
        """Test markdown output generation."""
        repo_stars = {
            'owner/repo1': {'count': 10, 'global_stars': 1000, 'description': 'Test repo 1', 'url': 'https://github.com/owner/repo1'},
            'owner/repo2': {'count': 5, 'global_stars': 500, 'description': 'Test repo 2', 'url': 'https://github.com/owner/repo2'}
        }
        
        user_follows = {
            'user1': 8,
            'user2': 3
        }
        
        hidden_gems = [
            ('owner/repo2', {'count': 5, 'global_stars': 500, 'description': 'Test repo 2', 'url': 'https://github.com/owner/repo2'})
        ]
        
        markdown = generate_markdown_output('testuser', 100, repo_stars, user_follows, hidden_gems)
        
        # Verify markdown structure
        self.assertIn('# GitHub Network Insight Report', markdown)
        self.assertIn('**Target User:** testuser', markdown)
        self.assertIn('**Audience Size:** 100', markdown)
        self.assertIn('## 📊 Top 10 Commonly Starred Repositories', markdown)
        self.assertIn('## 💎 Top 10 Hidden Gems', markdown)
        self.assertIn('## 👥 Top 10 Thought Leaders', markdown)
        
        # Verify markdown links
        self.assertIn('[owner/repo1](https://github.com/owner/repo1)', markdown)
        self.assertIn('[user1](https://github.com/user1)', markdown)
        
        # Verify table structure
        self.assertIn('| Rank | Repository | Network Stars | Global Stars | Description |', markdown)
        self.assertIn('|------|------------|---------------|--------------|-------------|', markdown)
    
    def test_is_safe_github_url(self):
        """Test GitHub URL validation."""
        # Valid GitHub URLs
        self.assertTrue(is_safe_github_url('https://github.com/user/repo'))
        self.assertTrue(is_safe_github_url('https://github.com/user'))
        
        # Invalid URLs
        self.assertFalse(is_safe_github_url(''))
        self.assertFalse(is_safe_github_url('http://github.com/user/repo'))  # Not HTTPS
        self.assertFalse(is_safe_github_url('https://evil.com/malicious'))
        self.assertFalse(is_safe_github_url('javascript:alert(1)'))
        self.assertFalse(is_safe_github_url(None))
    
    def test_escape_markdown_table_content(self):
        """Test markdown table content escaping."""
        self.assertEqual(escape_markdown_table_content('normal text'), 'normal text')
        self.assertEqual(escape_markdown_table_content('text | with | pipes'), 'text \\| with \\| pipes')
        self.assertEqual(escape_markdown_table_content(''), '')
        self.assertEqual(escape_markdown_table_content(None), '')


if __name__ == '__main__':
    unittest.main()
