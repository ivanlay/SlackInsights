# SlackInsights

An intelligent Slack bot that analyzes conversations across channels and generates AI-powered summaries focused on actionable insights, product feedback, and feature requests.

## Why This Exists

This bot was created to solve a real problem: At a company with over 100 customer-related Slack channels, it became nearly impossible for the product team to keep track of critical customer feedback scattered across conversations. Customer advocates, product managers, and support teams were discussing valuable insights in various channels, but important feedback was getting lost in the noise.

This bot automatically monitors all these channels, extracts the signal from the noise, and delivers a daily digest of actionable product feedback to a designated channel - ensuring that no critical customer insight goes unnoticed.

## Features

- 🤖 **Automated Channel Monitoring**: Monitors all channels the bot has access to
- 🧵 **Thread-Aware Processing**: Captures and includes thread replies in analysis
- 🎯 **Actionable Insights**: Focuses on product feedback, feature requests, and user pain points
- 📊 **Smart Filtering**: Excludes bot messages and irrelevant content
- 🔄 **Flexible Scheduling**: Configurable for daily or weekday-only runs
- 📝 **Formatted Summaries**: Posts well-structured summaries to a designated channel

## Prerequisites

- Python 3.8+
- Slack workspace with bot permissions
- OpenAI API access
- Slack Bot Token with the following OAuth scopes:
  - `channels:history`
  - `channels:read`
  - `chat:write`
  - `users:read`
  - `groups:history`
  - `groups:read`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ivanlay/slackinsights.git
cd slackinsights
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the environment template and configure:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:
```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
OPENAI_API_KEY=sk-your-openai-api-key
SUMMARY_CHANNEL=#product-feedback
IGNORE_CHANNELS=C1234567890,C0987654321
```

5. Test your setup:
```bash
python test_setup.py
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | `xoxb-123456789012-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `SUMMARY_CHANNEL` | Channel to post summaries | `#product-feedback` |
| `IGNORE_CHANNELS` | Comma-separated channel IDs to skip | `C1234567890,C0987654321` |
| `SUMMARY_TITLE` | Title for summary messages (optional) | `Customer Channel Summary` |
| `LOG_LEVEL` | Logging level (optional) | `INFO` |

### Bot Settings

In `slack_summary_bot.py`:
- `RUN_DAILY`: Set to `True` for daily runs, `False` to skip weekends

## Usage

### Manual Run
```bash
python slack_summary_bot.py
```

### Scheduled Execution

#### Using Cron (Unix/Linux/macOS)
```bash
# Add to crontab (runs daily at 9 AM)
0 9 * * * /usr/bin/python3 /path/to/slack_summary_bot.py
```

#### Using Task Scheduler (Windows)
Create a scheduled task to run the Python script at your desired interval.

### Docker Deployment
```bash
docker build -t slackinsights .
docker run --env-file .env slackinsights
```

## Use Cases

This bot is ideal for:

- **Large Organizations**: Companies with numerous customer-facing channels where product feedback gets scattered
- **Product Teams**: Who need to stay informed about customer feedback without monitoring dozens of channels
- **Customer Success Teams**: To ensure critical feedback reaches the product team
- **Support Organizations**: To identify recurring issues and feature requests from support conversations
- **Remote Teams**: Where async communication makes it hard to keep track of all discussions

## How It Works

1. **Channel Discovery**: Bot identifies all accessible channels (excluding configured ignore list)
2. **Message Collection**: Fetches messages from the last 24 hours (or 3 days on Mondays)
3. **Thread Processing**: Retrieves and includes thread replies for complete context
4. **AI Analysis**: OpenAI analyzes conversations for:
   - Product feedback (positive/negative)
   - Feature requests
   - User pain points
   - Improvement suggestions
5. **Summary Generation**: Creates concise, actionable bullet points
6. **Slack Posting**: Formats and posts summaries to the designated channel

## Example Output

```
Customer Channel Summary
━━━━━━━━━━━━━━━━━━━━━━
Channel: #customer-success (customer-success)
Summary:
• Feature Request: Add bulk user import functionality to streamline onboarding for enterprise clients
• User Pain Point: Dashboard loading times exceed 10 seconds for accounts with 1000+ integrations
• UX Improvement: Implement keyboard shortcuts for frequently used actions in the workflow builder
━━━━━━━━━━━━━━━━━━━━━━
```

## Customization

### Adjusting the AI Analysis

The bot's analysis can be customized by modifying the prompt in `slack_summary_bot.py`. Look for the comment `# You can customize this prompt for your specific use case` around line 236.

Example customizations:
- **Engineering Teams**: Focus on bug reports, technical debt, and performance issues
- **Sales Teams**: Extract customer objections, feature requests, and competitive intelligence
- **Support Teams**: Identify common problems, documentation gaps, and training needs
- **Marketing Teams**: Gather product testimonials, use cases, and customer success stories

### Channel Filtering

Beyond the `IGNORE_CHANNELS` setting, you can modify the channel selection logic in the `get_bot_channels()` function to:
- Only include channels matching a specific pattern (e.g., "customer-*")
- Exclude channels based on activity level
- Filter by channel purpose or topic

## Development

### Project Structure
```
slackinsights/
├── slack_summary_bot.py    # Main bot implementation
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
├── README.md              # This file
├── CONTRIBUTING.md        # Contribution guidelines
├── test_setup.py          # Configuration verification
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
└── docs/
    └── DEPLOYMENT.md      # Deployment guide
```

### Running Tests
```bash
python -m pytest tests/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## Security

- Never commit `.env` files or expose API tokens
- Regularly rotate API keys and tokens
- Review channel permissions to ensure appropriate access

## Troubleshooting

### Common Issues

1. **Bot not finding channels**: Ensure the bot is invited to channels and has proper permissions
2. **Empty summaries**: Check that channels have recent activity and aren't in the ignore list
3. **API errors**: Verify API keys are valid and have sufficient quota

### Debug Mode
Enable detailed logging by setting the log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for teams using Slack for customer communication
- Optimized for SaaS product development workflows
- Inspired by the need for actionable insights from customer conversations