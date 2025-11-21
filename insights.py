#!/usr/bin/env python3
"""
GitHub Network Insight Analyzer

Analyzes GitHub user networks to discover hidden gem repositories
and influential developers based on followers and stargazers.
"""

import os
import sys
import time
import argparse
import json
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class GitHubAPIClient:
    """GitHub API client with rate limiting support."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            console.print("[red]ERROR: GITHUB_TOKEN environment variable not set![/red]")
            console.print("Please set your GitHub token: export GITHUB_TOKEN=your_token")
            sys.exit(1)
        
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
    
    def _check_rate_limit(self, response: requests.Response):
        """Check and handle rate limiting."""
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if self.rate_limit_remaining < 10:
            wait_time = self.rate_limit_reset - time.time() + 5
            if wait_time > 0:
                console.print(f"[yellow]Rate limit low. Waiting {int(wait_time)} seconds...[/yellow]")
                time.sleep(wait_time)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a GET request to the GitHub API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            self._check_rate_limit(response)
            
            if response.status_code == 403 or response.status_code == 429:
                wait_time = 60
                console.print(f"[yellow]Rate limited. Waiting {wait_time} seconds...[/yellow]")
                time.sleep(wait_time)
                response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error fetching {endpoint}: {e}[/red]")
            return None
    
    def get_paginated(self, endpoint: str, per_page: int = 100, max_pages: Optional[int] = None) -> List[Dict]:
        """Fetch paginated results from GitHub API."""
        results = []
        page = 1
        
        while True:
            params = {'per_page': per_page, 'page': page}
            data = self.get(endpoint, params)
            
            if not data:
                break
            
            if isinstance(data, list):
                results.extend(data)
                if len(data) < per_page:
                    break
            else:
                results.append(data)
                break
            
            page += 1
            if max_pages and page > max_pages:
                break
        
        return results


class NetworkAnalyzer:
    """Analyzes GitHub networks to find recommendations."""
    
    def __init__(self, api_client: GitHubAPIClient, limit: int = 100, stars_per_user: int = 30):
        self.api = api_client
        self.limit = limit
        self.stars_per_user = stars_per_user
    
    def get_user_repos(self, username: str) -> List[Dict]:
        """Get all repositories for a user."""
        console.print(f"[cyan]Fetching repositories for {username}...[/cyan]")
        repos = self.api.get_paginated(f"/users/{username}/repos", per_page=100)
        console.print(f"[green]Found {len(repos)} repositories[/green]")
        return repos
    
    def get_stargazers(self, owner: str, repo: str, max_count: Optional[int] = None) -> List[str]:
        """Get stargazers for a repository."""
        stargazers = self.api.get_paginated(
            f"/repos/{owner}/{repo}/stargazers",
            per_page=100,
            max_pages=max_count // 100 + 1 if max_count else None
        )
        usernames = [s['login'] for s in stargazers if 'login' in s]
        if max_count:
            usernames = usernames[:max_count]
        return usernames
    
    def get_followers(self, username: str, max_count: Optional[int] = None) -> List[str]:
        """Get followers for a user."""
        console.print(f"[cyan]Fetching followers for {username}...[/cyan]")
        followers = self.api.get_paginated(
            f"/users/{username}/followers",
            per_page=100,
            max_pages=max_count // 100 + 1 if max_count else None
        )
        usernames = [f['login'] for f in followers if 'login' in f]
        if max_count:
            usernames = usernames[:max_count]
        console.print(f"[green]Found {len(usernames)} followers[/green]")
        return usernames
    
    def build_audience(self, username: str) -> Set[str]:
        """Build the audience list: followers + stargazers of user's repos."""
        audience = set()
        
        # Get followers
        followers = self.get_followers(username, self.limit)
        audience.update(followers)
        
        # Get stargazers from user's repositories
        repos = self.get_user_repos(username)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Collecting stargazers...", total=len(repos))
            
            for repo in repos:
                repo_name = repo['name']
                stargazers = self.get_stargazers(username, repo_name, max_count=100)
                audience.update(stargazers)
                progress.update(task, advance=1)
        
        # Remove the target user from audience
        audience.discard(username)
        
        console.print(f"[green]Total unique audience members: {len(audience)}[/green]")
        return audience
    
    def analyze_network_stars(self, audience: Set[str]) -> Dict[str, Dict]:
        """Analyze what repositories the network has starred."""
        repo_stars = defaultdict(lambda: {'count': 0, 'description': '', 'global_stars': 0, 'url': ''})
        
        # Limit audience for analysis
        audience_list = list(audience)[:self.limit]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Analyzing starred repos from {len(audience_list)} users...",
                total=len(audience_list)
            )
            
            for user in audience_list:
                starred = self.api.get_paginated(
                    f"/users/{user}/starred",
                    per_page=self.stars_per_user,
                    max_pages=1
                )
                
                for repo in starred[:self.stars_per_user]:
                    if repo and 'full_name' in repo:
                        full_name = repo['full_name']
                        repo_stars[full_name]['count'] += 1
                        repo_stars[full_name]['description'] = repo.get('description', '')
                        repo_stars[full_name]['global_stars'] = repo.get('stargazers_count', 0)
                        repo_stars[full_name]['url'] = repo.get('html_url', '')
                
                progress.update(task, advance=1)
        
        return dict(repo_stars)
    
    def analyze_network_following(self, audience: Set[str]) -> Dict[str, int]:
        """Analyze who the network follows."""
        user_follows = defaultdict(int)
        
        # Limit audience for analysis
        audience_list = list(audience)[:self.limit]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Analyzing followed users from {len(audience_list)} users...",
                total=len(audience_list)
            )
            
            for user in audience_list:
                following = self.api.get_paginated(
                    f"/users/{user}/following",
                    per_page=100,
                    max_pages=1
                )
                
                for followed_user in following[:100]:
                    if followed_user and 'login' in followed_user:
                        username = followed_user['login']
                        user_follows[username] += 1
                
                progress.update(task, advance=1)
        
        return dict(user_follows)
    
    def filter_hidden_gems(self, repo_stars: Dict[str, Dict], threshold: int = 5000) -> List[Tuple[str, Dict]]:
        """Filter repos that are hidden gems (high network overlap, lower global popularity)."""
        gems = []
        for repo_name, data in repo_stars.items():
            if data['global_stars'] < threshold and data['count'] >= 2:
                gems.append((repo_name, data))
        
        # Sort by network stars
        gems.sort(key=lambda x: x[1]['count'], reverse=True)
        return gems


def print_text_report(target_user: str, audience_size: int, repo_stars: Dict[str, Dict], 
                     user_follows: Dict[str, int], hidden_gems: List[Tuple[str, Dict]]):
    """Print a formatted text report."""
    console.print("\n" + "="*80)
    console.print(f"[bold cyan]GitHub Network Insight Report for: {target_user}[/bold cyan]")
    console.print(f"[cyan]Audience Size: {audience_size}[/cyan]")
    console.print("="*80 + "\n")
    
    # Top Commonly Starred Repos
    console.print("[bold yellow]📊 Top 10 Commonly Starred Repositories (Crowd Favorites)[/bold yellow]\n")
    
    sorted_repos = sorted(repo_stars.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Repository", style="cyan")
    table.add_column("Network Stars", justify="right", style="green")
    table.add_column("Global Stars", justify="right", style="yellow")
    table.add_column("Description", style="white")
    
    for idx, (repo_name, data) in enumerate(sorted_repos, 1):
        desc = data['description'][:60] + "..." if data['description'] and len(data['description']) > 60 else data['description'] or ""
        table.add_row(
            str(idx),
            repo_name,
            str(data['count']),
            str(data['global_stars']),
            desc
        )
    
    console.print(table)
    console.print()
    
    # Hidden Gems
    console.print("[bold yellow]💎 Top 10 Hidden Gems (High Network Overlap, Lower Global Popularity)[/bold yellow]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Repository", style="cyan")
    table.add_column("Network Stars", justify="right", style="green")
    table.add_column("Global Stars", justify="right", style="yellow")
    table.add_column("Description", style="white")
    
    for idx, (repo_name, data) in enumerate(hidden_gems[:10], 1):
        desc = data['description'][:60] + "..." if data['description'] and len(data['description']) > 60 else data['description'] or ""
        table.add_row(
            str(idx),
            repo_name,
            str(data['count']),
            str(data['global_stars']),
            desc
        )
    
    console.print(table)
    console.print()
    
    # Influential People
    console.print("[bold yellow]👥 Top 10 Thought Leaders (People Followed by Your Audience)[/bold yellow]\n")
    
    sorted_users = sorted(user_follows.items(), key=lambda x: x[1], reverse=True)[:10]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Username", style="cyan")
    table.add_column("Network Follows", justify="right", style="green")
    table.add_column("Profile URL", style="blue")
    
    for idx, (username, count) in enumerate(sorted_users, 1):
        table.add_row(
            str(idx),
            username,
            str(count),
            f"https://github.com/{username}"
        )
    
    console.print(table)
    console.print()


def generate_json_output(target_user: str, audience_size: int, repo_stars: Dict[str, Dict],
                        user_follows: Dict[str, int], hidden_gems: List[Tuple[str, Dict]]) -> Dict:
    """Generate JSON output."""
    sorted_repos = sorted(repo_stars.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
    sorted_users = sorted(user_follows.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "target_user": target_user,
        "audience_size": audience_size,
        "recommendations": {
            "repositories": [
                {
                    "name": repo_name,
                    "url": data['url'],
                    "network_stars": data['count'],
                    "global_stars": data['global_stars'],
                    "description": data['description']
                }
                for repo_name, data in sorted_repos
            ],
            "hidden_gems": [
                {
                    "name": repo_name,
                    "url": data['url'],
                    "network_stars": data['count'],
                    "global_stars": data['global_stars'],
                    "description": data['description']
                }
                for repo_name, data in hidden_gems[:10]
            ],
            "people": [
                {
                    "username": username,
                    "network_follows": count,
                    "url": f"https://github.com/{username}"
                }
                for username, count in sorted_users
            ]
        }
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='GitHub Network Insight Analyzer - Discover hidden gems and influential developers'
    )
    parser.add_argument('username', help='GitHub username to analyze')
    parser.add_argument('--limit', type=int, default=100,
                       help='Maximum number of network members to analyze (default: 100)')
    parser.add_argument('--stars-per-user', type=int, default=30,
                       help='Maximum starred repos to fetch per user (default: 30)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output-file', help='Save JSON output to file (only with --output json)')
    
    args = parser.parse_args()
    
    # Initialize API client
    api_client = GitHubAPIClient()
    
    # Verify user exists
    user_data = api_client.get(f"/users/{args.username}")
    if not user_data:
        console.print(f"[red]Error: User '{args.username}' not found or is private[/red]")
        sys.exit(1)
    
    console.print(f"[green]✓ Found user: {args.username}[/green]\n")
    
    # Initialize analyzer
    analyzer = NetworkAnalyzer(api_client, limit=args.limit, stars_per_user=args.stars_per_user)
    
    # Step 1: Build audience
    audience = analyzer.build_audience(args.username)
    
    if len(audience) == 0:
        console.print("[yellow]Warning: No audience found for this user[/yellow]")
        sys.exit(0)
    
    # Step 2: Analyze network stars
    repo_stars = analyzer.analyze_network_stars(audience)
    
    # Filter out target user's own repos
    repo_stars = {k: v for k, v in repo_stars.items() if not k.startswith(f"{args.username}/")}
    
    # Step 3: Analyze network following
    user_follows = analyzer.analyze_network_following(audience)
    
    # Filter out target user
    user_follows = {k: v for k, v in user_follows.items() if k != args.username}
    
    # Step 4: Find hidden gems
    hidden_gems = analyzer.filter_hidden_gems(repo_stars)
    
    # Step 5: Output results
    if args.output == 'json':
        output = generate_json_output(args.username, len(audience), repo_stars, user_follows, hidden_gems)
        json_str = json.dumps(output, indent=2)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(json_str)
            console.print(f"[green]✓ Results saved to {args.output_file}[/green]")
        else:
            print(json_str)
    else:
        print_text_report(args.username, len(audience), repo_stars, user_follows, hidden_gems)
    
    console.print(f"\n[green]✓ Analysis complete![/green]")
    console.print(f"[dim]API calls remaining: {api_client.rate_limit_remaining}[/dim]\n")


if __name__ == '__main__':
    main()
