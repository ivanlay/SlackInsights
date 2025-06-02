# Deployment Guide

This guide covers various ways to deploy the Slack Summary Bot in production.

## Table of Contents
- [Docker Deployment](#docker-deployment)
- [Systemd Service (Linux)](#systemd-service-linux)
- [Cron Job](#cron-job)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)

## Docker Deployment

### Single Run with Docker

```bash
# Build the image
docker build -t slack-summary-bot .

# Run once
docker run --env-file .env slack-summary-bot
```

### Docker Compose with Scheduling

1. For scheduled runs with cron:
```bash
# Add to host's crontab
0 9 * * * cd /path/to/slack-summary-bot && docker-compose run --rm slack-summary-bot
```

2. For continuous running with internal scheduling:
```yaml
# Uncomment the command line in docker-compose.yml
command: sh -c "while true; do python slack_summary_bot.py; sleep 86400; done"
```

Then run:
```bash
docker-compose up -d
```

## Systemd Service (Linux)

1. Create a service file `/etc/systemd/system/slack-summary-bot.service`:

```ini
[Unit]
Description=Slack Summary Bot
After=network.target

[Service]
Type=oneshot
User=slackbot
WorkingDirectory=/opt/slack-summary-bot
Environment="PATH=/opt/slack-summary-bot/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/slack-summary-bot/venv/bin/python /opt/slack-summary-bot/slack_summary_bot.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

2. Create a timer file `/etc/systemd/system/slack-summary-bot.timer`:

```ini
[Unit]
Description=Run Slack Summary Bot daily
Requires=slack-summary-bot.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. Setup and enable:

```bash
# Create user and directory
sudo useradd -r -s /bin/false slackbot
sudo mkdir -p /opt/slack-summary-bot
sudo chown slackbot:slackbot /opt/slack-summary-bot

# Copy files and setup virtual environment
sudo -u slackbot cp -r * /opt/slack-summary-bot/
cd /opt/slack-summary-bot
sudo -u slackbot python3 -m venv venv
sudo -u slackbot venv/bin/pip install -r requirements.txt

# Copy and configure .env
sudo cp .env.example /opt/slack-summary-bot/.env
sudo chown slackbot:slackbot /opt/slack-summary-bot/.env
sudo chmod 600 /opt/slack-summary-bot/.env
# Edit /opt/slack-summary-bot/.env with your credentials

# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable slack-summary-bot.timer
sudo systemctl start slack-summary-bot.timer

# Check status
sudo systemctl status slack-summary-bot.timer
sudo systemctl list-timers
```

## Cron Job

### Simple Cron Setup

1. Edit crontab:
```bash
crontab -e
```

2. Add entry (runs daily at 9 AM):
```cron
# Slack Summary Bot
0 9 * * * cd /path/to/slack-summary-bot && /path/to/venv/bin/python slack_summary_bot.py >> /var/log/slack-summary-bot.log 2>&1
```

### Advanced Cron with Error Handling

Create a wrapper script `/usr/local/bin/slack-summary-bot-wrapper.sh`:

```bash
#!/bin/bash
set -e

# Configuration
BOT_DIR="/opt/slack-summary-bot"
VENV_PATH="${BOT_DIR}/venv"
LOG_FILE="/var/log/slack-summary-bot/bot.log"
ERROR_LOG="/var/log/slack-summary-bot/error.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Activate virtual environment and run bot
cd "$BOT_DIR"
source "${VENV_PATH}/bin/activate"

# Run with timeout and error handling
timeout 3600 python slack_summary_bot.py >> "$LOG_FILE" 2>> "$ERROR_LOG"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "[$(date)] Bot failed with exit code $EXIT_CODE" >> "$ERROR_LOG"
    # Optional: Send alert via email or Slack
fi

exit $EXIT_CODE
```

Then add to crontab:
```cron
0 9 * * * /usr/local/bin/slack-summary-bot-wrapper.sh
```

## Cloud Deployment

### AWS Lambda

1. Create `lambda_handler.py`:
```python
import asyncio
from slack_summary_bot import main

def lambda_handler(event, context):
    asyncio.run(main())
    return {
        'statusCode': 200,
        'body': 'Summary completed successfully'
    }
```

2. Package and deploy:
```bash
# Install dependencies to a directory
pip install -r requirements.txt -t package/
cp slack_summary_bot.py lambda_handler.py package/
cd package && zip -r ../deployment.zip .
```

3. Schedule with CloudWatch Events (cron expression: `0 9 * * ? *`)

### Google Cloud Functions

1. Create `main.py`:
```python
import asyncio
from slack_summary_bot import main as bot_main

def slack_summary_bot(request):
    asyncio.run(bot_main())
    return 'Summary completed successfully', 200
```

2. Deploy:
```bash
gcloud functions deploy slack-summary-bot \
    --runtime python311 \
    --trigger-http \
    --entry-point slack_summary_bot \
    --env-vars-file .env.yaml
```

3. Schedule with Cloud Scheduler

### Heroku

1. Create `Procfile`:
```
worker: python slack_summary_bot.py
```

2. Deploy and schedule with Heroku Scheduler add-on

## Monitoring

### Health Checks

Add a health check endpoint by creating `health_check.py`:

```python
import os
import asyncio
from slack_sdk.web.async_client import AsyncWebClient

async def check_health():
    """Verify bot can connect to Slack and OpenAI."""
    try:
        # Check Slack connection
        slack_client = AsyncWebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        await slack_client.auth_test()
        
        # Check OpenAI connection
        from openai import AsyncOpenAI
        openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Simple test - you might want to adjust based on your needs
        
        return True, "All systems operational"
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

if __name__ == "__main__":
    success, message = asyncio.run(check_health())
    print(f"Health Check: {'PASS' if success else 'FAIL'} - {message}")
    exit(0 if success else 1)
```

### Logging and Monitoring

1. **Centralized Logging**: Configure LOG_LEVEL and forward logs to a service like:
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Datadog
   - CloudWatch Logs
   - Papertrail

2. **Metrics**: Track:
   - Execution time
   - Number of channels processed
   - Summary generation success/failure rate
   - API rate limits

3. **Alerts**: Set up alerts for:
   - Failed executions
   - API errors
   - Unusual execution times
   - Missing scheduled runs

### Example Monitoring Script

```bash
#!/bin/bash
# monitor-slack-bot.sh

# Run the bot and capture exit code
/opt/slack-summary-bot/venv/bin/python /opt/slack-summary-bot/slack_summary_bot.py
EXIT_CODE=$?

# Send metrics (example with curl to a monitoring endpoint)
curl -X POST https://monitoring.example.com/metrics \
  -H "Content-Type: application/json" \
  -d "{
    \"service\": \"slack-summary-bot\",
    \"status\": \"$EXIT_CODE\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }"

exit $EXIT_CODE
```

## Security Best Practices

1. **Environment Variables**: 
   - Never commit `.env` files
   - Use secrets management services in production
   - Rotate API keys regularly

2. **File Permissions**:
   ```bash
   chmod 600 .env
   chmod 700 slack_summary_bot.py
   ```

3. **Network Security**:
   - Run in isolated network when possible
   - Use egress firewall rules to only allow Slack and OpenAI APIs

4. **Updates**:
   - Regularly update dependencies
   - Monitor for security advisories