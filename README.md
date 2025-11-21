# GitHub Network Insight Analyzer

Discover "hidden gem" repositories and influential developers based on your GitHub audience.

## Overview

This tool analyzes the intersection of interest among a user's **Stargazers** and **Followers** to generate a prioritized list of recommended repositories and users.

## Features

- **Network Analysis**: Identifies your GitHub network (followers + stargazers)
- **Repository Recommendations**: Discovers repos popular among your network
- **Influential People**: Identifies thought leaders followed by your audience
- **Hidden Gems**: Highlights lesser-known repos with high network overlap

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Set your GitHub token as an environment variable:
```bash
export GITHUB_TOKEN=your_github_token_here
```

Run the analyzer:
```bash
python insights.py <username>
```

### Options

- `--limit N`: Limit the number of network members to analyze (default: 100)
- `--stars-per-user N`: Max starred repos to fetch per user (default: 30)
- `--format FORMAT`: Terminal output format (text or json, default: text)
- `--output FILENAME`: Save output to markdown file (in addition to terminal output)

### Example

```bash
python insights.py agileandy --limit 50
```

### Save to Markdown File

Save results to a markdown file in addition to terminal output:

```bash
python insights.py agileandy --output results.md
```

This will display the results in the terminal and save a markdown version to `results.md`.

## Requirements

- Python 3.7+
- GitHub Personal Access Token (for API access)
- See `requirements.txt` for Python dependencies

## API Rate Limits

- **Unauthenticated**: 60 requests/hour (insufficient for this tool)
- **Authenticated**: 5,000 requests/hour (required)

## License

See LICENSE file for details.
