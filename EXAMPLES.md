# Example Usage Guide

This guide demonstrates how to use the GitHub Network Insight Analyzer.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a GitHub Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `public_repo`, `read:user`
   - Generate and copy the token

3. **Set the token as an environment variable:**
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

## Basic Usage

### Analyze a GitHub User

```bash
python insights.py agileandy
```

This will:
- Collect all followers and stargazers of agileandy's repositories
- Analyze what repositories they have starred
- Analyze who they follow
- Display a report with recommendations

### Limit Network Size

For users with large networks, limit the analysis:

```bash
python insights.py agileandy --limit 50
```

This analyzes only the first 50 network members.

### Adjust Stars Per User

Control how many starred repos to fetch per network member:

```bash
python insights.py agileandy --stars-per-user 20
```

Default is 30 stars per user.

### JSON Output

Get results in JSON format:

```bash
python insights.py agileandy --output json
```

### Save to File

Save JSON output to a file:

```bash
python insights.py agileandy --output json --output-file results.json
```

## Example Output

### Text Format (Default)

```
================================================================================
GitHub Network Insight Report for: agileandy
Audience Size: 150
================================================================================

📊 Top 10 Commonly Starred Repositories (Crowd Favorites)

┏━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Repository        ┃ Network Stars┃ Global Stars ┃ Description    ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 1    │ torvalds/linux    │ 12           │ 150000       │ Linux kernel   │
│ 2    │ vercel/next.js    │ 10           │ 120000       │ React framework│
└──────┴───────────────────┴──────────────┴──────────────┴────────────────┘

💎 Top 10 Hidden Gems (High Network Overlap, Lower Global Popularity)

┏━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Repository        ┃ Network Stars┃ Global Stars ┃ Description    ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 1    │ user/hidden-tool  │ 8            │ 450          │ Useful utility │
└──────┴───────────────────┴──────────────┴──────────────┴────────────────┘

👥 Top 10 Thought Leaders (People Followed by Your Audience)

┏━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Username      ┃ Network Follows┃ Profile URL                     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ tjholowaychuk │ 8              │ https://github.com/tjholowaychuk│
└──────┴───────────────┴────────────────┴────────────────────────────────┘
```

### JSON Format

```json
{
  "target_user": "agileandy",
  "audience_size": 150,
  "recommendations": {
    "repositories": [
      {
        "name": "torvalds/linux",
        "url": "https://github.com/torvalds/linux",
        "network_stars": 12,
        "global_stars": 150000,
        "description": "Linux kernel source tree"
      }
    ],
    "hidden_gems": [
      {
        "name": "user/hidden-tool",
        "url": "https://github.com/user/hidden-tool",
        "network_stars": 8,
        "global_stars": 450,
        "description": "A useful utility for developers"
      }
    ],
    "people": [
      {
        "username": "tjholowaychuk",
        "network_follows": 8,
        "url": "https://github.com/tjholowaychuk"
      }
    ]
  }
}
```

## Understanding the Results

### Commonly Starred Repositories
These are the most popular repositories among your network. High network stars and high global stars indicate crowd favorites.

### Hidden Gems
These repositories have:
- Lower global popularity (< 5,000 stars by default)
- High overlap with your network (starred by 2+ network members)

These are often niche tools or libraries that are highly relevant to your specific community.

### Thought Leaders
People who are followed by many members of your network. These individuals may be worth following for insights relevant to your community.

## Tips

1. **Start Small**: For first-time use, use `--limit 20` to quickly test the tool
2. **Be Patient**: Analyzing large networks can take several minutes due to API rate limits
3. **Monitor Rate Limits**: The tool displays remaining API calls at the end
4. **Save Results**: Use `--output json --output-file` to save results for later analysis

## Troubleshooting

### "Rate limit low" messages
The tool will automatically wait and retry when approaching rate limits.

### "User not found or is private"
Verify the username is correct and the user's profile is public.

### Long execution time
Large networks can take 5-15 minutes. Use `--limit` to reduce analysis time.
