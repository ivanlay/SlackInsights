FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY slack_summary_bot.py .

# Create non-root user
RUN useradd -m -u 1000 slackbot && chown -R slackbot:slackbot /app
USER slackbot

# Run the bot
CMD ["python", "slack_summary_bot.py"]