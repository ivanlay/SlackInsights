import os
from datetime import datetime, timedelta
import json
import logging
from typing import List, Tuple, Dict, Optional
import asyncio

import aiohttp
from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configuration
SUMMARY_CHANNEL = os.getenv("SUMMARY_CHANNEL")
IGNORE_CHANNELS = (
    os.getenv("IGNORE_CHANNELS", "").split(",") if os.getenv("IGNORE_CHANNELS") else []
)
SUMMARY_TITLE = os.getenv("SUMMARY_TITLE", "Customer Channel Summary")

RUN_DAILY = True  # Set to True for daily runs, False to skip weekends

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = {
        "SLACK_BOT_TOKEN": "Slack bot token",
        "OPENAI_API_KEY": "OpenAI API key",
        "SUMMARY_CHANNEL": "Summary channel",
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please copy .env.example to .env and fill in all required values")
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Validate SUMMARY_CHANNEL format
    if SUMMARY_CHANNEL and not SUMMARY_CHANNEL.startswith("#"):
        logger.warning(
            f"SUMMARY_CHANNEL should start with '#'. Current value: {SUMMARY_CHANNEL}"
        )


# Initialize clients - will be done in main()
client = None
openai_client = None


async def get_bot_channels() -> Tuple[Optional[str], List[Dict[str, str]]]:
    """
    Fetch the channels the bot is a member of.

    Returns:
        A tuple containing the bot's user ID and a list of channel dictionaries.
    """
    try:
        auth_result = await client.auth_test()
        bot_user_id = auth_result["user_id"]

        result = await client.users_conversations(
            user=bot_user_id, types="public_channel,private_channel"
        )

        channels = [
            {"id": channel["id"], "name": channel["name"]}
            for channel in result["channels"]
            if channel.get("name") != SUMMARY_CHANNEL.lstrip("#")
            and channel.get("id") not in IGNORE_CHANNELS
        ]
        return bot_user_id, channels
    except SlackApiError as e:
        logger.error(f"Error fetching bot channels: {e.response['error']}")
        return None, []


def get_time_range() -> Tuple[datetime, datetime]:
    """
    Calculate the time range for fetching messages.

    Returns:
        A tuple containing the start and end datetime objects.
    """
    end_time = datetime.now()

    if RUN_DAILY:
        start_time = end_time - timedelta(days=1)
    else:
        if end_time.weekday() == 0:  # Monday
            start_time = end_time - timedelta(days=3)
        elif end_time.weekday() in [5, 6]:  # Saturday or Sunday
            return None, None  # Skip execution on weekends
        else:
            start_time = end_time - timedelta(days=1)

    return start_time, end_time


async def fetch_messages(
    channel_id: str, start_time: datetime, end_time: datetime
) -> List[Dict[str, str]]:
    """
    Fetch messages from a Slack channel within a specified time range.

    Args:
        channel_id (str): The ID of the Slack channel.
        start_time (datetime): The start time for fetching messages.
        end_time (datetime): The end time for fetching messages.

    Returns:
        A list of message dictionaries.
    """
    messages = []
    try:
        result = await client.conversations_history(
            channel=channel_id,
            oldest=str(start_time.timestamp()),
            latest=str(end_time.timestamp()),
        )
        messages = result["messages"]
    except SlackApiError as e:
        logger.error(
            f"Error fetching messages for channel {channel_id}: {e.response.get('error', str(e))}"
        )
    return messages


async def fetch_thread_replies(
    channel_id: str, thread_ts: str, bot_user_id: str
) -> List[Dict[str, str]]:
    """
    Fetch replies to a thread in a Slack channel.

    Args:
        channel_id (str): The ID of the Slack channel.
        thread_ts (str): The timestamp of the parent message.
        bot_user_id (str): The user ID of the bot.

    Returns:
        A list of formatted reply messages.
    """
    try:
        result = await client.conversations_replies(channel=channel_id, ts=thread_ts)
        replies = format_messages(result["messages"][1:], bot_user_id)
        return replies
    except SlackApiError as e:
        logger.error(
            f"Error fetching thread replies for ts {thread_ts}: {e.response.get('error', str(e))}"
        )
        return []


def format_messages(
    messages: List[Dict[str, str]], bot_user_id: str
) -> List[Dict[str, str]]:
    """
    Format raw Slack messages into a consistent structure.

    Args:
        messages (list): A list of raw message dictionaries from Slack API.
        bot_user_id (str): The user ID of the bot.

    Returns:
        A list of formatted message dictionaries.
    """
    formatted_messages = []
    for message in messages:
        if (
            message.get("type") == "message"
            and (
                not message.get("subtype")
                or message.get("subtype") == "thread_broadcast"
            )
            and message.get("user") != bot_user_id
        ):
            formatted_message = {
                "user": message.get("user", ""),
                "text": message.get("text", ""),
                "ts": message.get("ts", ""),
                "thread_ts": message.get("thread_ts", ""),
            }
            formatted_messages.append(formatted_message)
    formatted_messages.sort(key=lambda x: float(x["ts"]))
    return formatted_messages


def update_message_list(
    message_list: List[Dict[str, str]],
    threaded_messages: List[Dict[str, str]],
    parent_ts: str,
) -> List[Dict[str, str]]:
    """
    Insert threaded messages into the main message list.

    Args:
        message_list (list): The main list of messages.
        threaded_messages (list): The list of threaded replies.
        parent_ts (str): The timestamp of the parent message.

    Returns:
        The updated message list with threaded replies inserted.
    """
    threaded_messages.sort(key=lambda x: float(x["ts"]))
    parent_index = next(
        (i for i, msg in enumerate(message_list) if msg["ts"] == parent_ts), -1
    )
    if parent_index != -1:
        message_list[parent_index + 1 : parent_index + 1] = threaded_messages
    return message_list


async def process_messages(
    channel_id: str, messages: List[Dict[str, str]], bot_user_id: str
) -> List[Dict[str, str]]:
    """
    Process messages from a channel, including fetching and inserting thread replies.

    Args:
        channel_id (str): The ID of the Slack channel.
        messages (list): The list of raw messages from the channel.
        bot_user_id (str): The user ID of the bot.

    Returns:
        A list of processed messages, including threaded replies.
    """
    processed_messages = format_messages(messages, bot_user_id)
    for i, message in enumerate(processed_messages):
        if message.get("thread_ts") and message["thread_ts"] == message["ts"]:
            replies = await fetch_thread_replies(channel_id, message["ts"], bot_user_id)
            processed_messages = update_message_list(
                processed_messages, replies, message["ts"]
            )
    return processed_messages


async def get_summary_from_openai(
    session: aiohttp.ClientSession, channel_data: List[Dict[str, str]]
) -> str:
    """
    Get a summary of the channel data from OpenAI using the Python client.

    Args:
        session (aiohttp.ClientSession): An aiohttp client session (not used with new approach).
        channel_data (list): A list of processed messages from the channel.

    Returns:
        A summary of the channel data.
    """
    try:
        slack_conversation = json.dumps(channel_data)

        # You can customize this prompt for your specific use case
        # For example: focus on bug reports, sales feedback, technical issues, etc.
        prompt = f"""You are an AI assistant specializing in product development analysis. Your task is to review a Slack conversation and provide actionable feedback for the product development team.

Here's the Slack conversation you need to analyze:

<slack_conversation>
{slack_conversation}
</slack_conversation>

Your goal is to extract valuable insights from this discussion and present them in a concise summary. Follow these steps:

1. Read the entire Slack conversation carefully.

2. Identify mentions of:
   a) Product feedback (positive or negative)
   b) Feature requests
   c) User pain points or frustrations
   d) Suggestions for improvement

3. Analyze the identified points to determine which are most actionable and relevant for the product development team.

4. Synthesize the key insights into a concise summary of 1-3 bullet points, one sentence each.

Before providing your final summary, wrap your analysis in <analysis> tags. In this section:

a) List relevant quotes from the Slack conversation for each category (product feedback, feature requests, user pain points, suggestions for improvement).
b) Evaluate each quote's relevance and actionability for the product development team.
c) Identify recurring themes or urgent issues.
d) Consider how the feedback aligns with your product's core functions and goals.

This will help ensure a thorough interpretation of the data.

Guidelines for your analysis:
- Prioritize concrete suggestions over vague complaints
- Focus on recurring themes or issues mentioned by multiple users
- Highlight any urgent problems that require immediate attention
- Include potential feature ideas that align with the product's core functions and goals
- Consider how the feedback relates to your product's core functions and strategic goals

When writing your final summary:
- Begin each bullet point with a descriptive phrase in asterisks (e.g., "*UX Improvement*:", "*User Pain Point*:", "*Feature Request*:", "*Product Win*:")
- Be concise and to the point
- Use clear, professional language
- Avoid technical jargon unless it's necessary for understanding the feedback
- Present the information in a way that's easy for the product team to act upon
- Focus solely on product feedback and feature requests related to your product
- Ensure each bullet point is one sentence long

Example output format (do not use this content, it's just to illustrate the structure):

- *Feature Request*: Users want the ability to export data in multiple formats for better integration.
- *User Pain Point*: Loading times are slow when dealing with large datasets.
- *UX Improvement*: The navigation menu should be more intuitive for first-time users.

After writing your summary, count the number of bullet points and sentences to ensure it meets the requirements of 1-3 bullet points, with one sentence each. Do not include the count in your response.

If no relevant summary is possible based on the Slack conversation, respond with <EXCLUDE>.

Please proceed with your analysis and summary of the Slack conversation.
"""

        response = await openai_client.responses.create(
            model="gpt-4.1-mini", input=prompt
        )

        # Extract text from the response
        if response.output and len(response.output) > 0:
            for item in response.output:
                if item.content and len(item.content) > 0:
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            # Process the response to remove <analysis> section
                            full_text = content_item.text

                            # Check for <EXCLUDE> outside of <analysis> tags
                            if (
                                "<EXCLUDE>" in full_text
                                and "<analysis>" not in full_text
                            ):
                                return "<EXCLUDE>"

                            # Remove the <analysis> section if present
                            analysis_start = full_text.find("<analysis>")
                            analysis_end = full_text.find("</analysis>")

                            if analysis_start != -1 and analysis_end != -1:
                                # Extract content before analysis
                                before_analysis = full_text[:analysis_start].strip()
                                # Extract content after analysis
                                after_analysis = full_text[
                                    analysis_end + 11 :
                                ].strip()  # 11 is the length of "</analysis>"

                                # Combine content, ignoring the analysis section
                                processed_text = (
                                    before_analysis + " " + after_analysis
                                ).strip()
                                return processed_text

                            return full_text

        return "<EXCLUDE>"

    except Exception as e:
        logger.error(f"Error getting summary from OpenAI: {e}")
        return f"Error getting summary: {str(e)}"


async def get_summary(
    session: aiohttp.ClientSession, channel_data: List[Dict[str, str]]
) -> str:
    """
    Wrapper function to get a summary of the channel data.

    Args:
        session (aiohttp.ClientSession): An aiohttp client session (not used with new approach).
        channel_data (list): A list of processed messages from the channel.

    Returns:
        A summary of the channel data.
    """
    return await get_summary_from_openai(session, channel_data)


def create_slack_message_blocks(
    summary_data: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Create Slack message blocks from the summary data.

    Args:
        summary_data (list): A list of dictionaries containing channel summaries.

    Returns:
        A list of Slack message blocks.
    """
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{SUMMARY_TITLE}*"}},
        {"type": "divider"},
    ]

    for data in summary_data:
        if data["summary"].strip() and data["summary"] != "<EXCLUDE>":
            blocks.extend(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Channel*: <#{data['id']}> ({data['name']})",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Summary*:\n{data['summary']}",
                        },
                    },
                    {"type": "divider"},
                ]
            )

    if not blocks[2:]:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No significant product feedback or feature requests in any customer channels today.",
                },
            }
        )

    return blocks


async def process_channels(
    channels: List[Dict[str, str]], bot_user_id: str
) -> List[Dict[str, str]]:
    """
    Process messages from multiple channels.

    Args:
        channels (list): A list of channel dictionaries to process.
        bot_user_id (str): The user ID of the bot.

    Returns:
        A list of dictionaries containing processed channel data.
    """
    start_time, end_time = get_time_range()
    tasks = [
        fetch_messages(channel["id"], start_time, end_time) for channel in channels
    ]
    results = await asyncio.gather(*tasks)

    channel_data = []
    for channel, messages in zip(channels, results):
        processed_messages = await process_messages(
            channel["id"], messages, bot_user_id
        )
        channel_info = {
            "id": channel["id"],
            "name": channel["name"],
            "messages": processed_messages,
            "summary": "",
        }
        channel_data.append(channel_info)

    return channel_data


async def main() -> None:
    """
    Main function to run the Slack bot.

    This function orchestrates the entire process of fetching messages,
    generating summaries, and posting the results to a Slack channel.
    """
    global client, openai_client

    try:
        # Initialize clients
        validate_config()
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        client = AsyncWebClient(token=slack_token)
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Check time range first
        start_time, end_time = get_time_range()
        if start_time is None:
            logger.info("Skipping execution on weekend (RUN_DAILY=False)")
            return

        logger.info(
            f"Starting SlackInsights - analyzing messages from {start_time} to {end_time}"
        )

        bot_user_id, channels = await get_bot_channels()
        if not bot_user_id:
            logger.error("Failed to get bot user ID. Check your SLACK_BOT_TOKEN.")
            raise ValueError("Invalid Slack bot token")

        logger.info(f"Found {len(channels)} channels to analyze")

        channel_data = await process_channels(channels, bot_user_id)

        # Create a dummy session to maintain compatibility with existing function signatures
        async with aiohttp.ClientSession() as session:
            tasks = [
                asyncio.create_task(get_summary(session, channel["messages"]))
                for channel in channel_data
                if channel["messages"]
            ]

            summaries = await asyncio.gather(*tasks)

            for channel, summary in zip(
                (c for c in channel_data if c["messages"]), summaries
            ):
                channel["summary"] = summary

        blocks = create_slack_message_blocks(channel_data)

        try:
            await client.chat_postMessage(
                channel=SUMMARY_CHANNEL, blocks=blocks, text=SUMMARY_TITLE
            )
            logger.info(f"Summary posted successfully to {SUMMARY_CHANNEL}")
        except SlackApiError as e:
            logger.error(
                f"Error posting message to {SUMMARY_CHANNEL}: {e.response.get('error', str(e))}"
            )
            raise

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot failed with error: {e}")
        raise
