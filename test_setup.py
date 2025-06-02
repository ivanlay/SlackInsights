#!/usr/bin/env python3
"""
Test script to verify Slack Summary Bot setup and configuration.
Run this before deploying to ensure everything is configured correctly.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

async def test_slack_connection():
    """Test Slack API connection and permissions."""
    print("🔍 Testing Slack connection...")
    
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print("❌ SLACK_BOT_TOKEN not found in environment variables")
        return False
    
    client = AsyncWebClient(token=token)
    
    try:
        # Test authentication
        auth_result = await client.auth_test()
        print(f"✅ Successfully authenticated as: {auth_result['user']} (Bot ID: {auth_result['user_id']})")
        
        # Test required permissions
        print("\n📋 Checking permissions...")
        
        # Test channel reading
        try:
            result = await client.users_conversations(limit=1)
            print("✅ Can read channels")
        except SlackApiError as e:
            print(f"❌ Cannot read channels: {e.response['error']}")
            return False
        
        # Test message reading (using the first channel found)
        if result['channels']:
            try:
                channel_id = result['channels'][0]['id']
                await client.conversations_history(channel=channel_id, limit=1)
                print("✅ Can read channel messages")
            except SlackApiError as e:
                print(f"❌ Cannot read messages: {e.response['error']}")
                return False
        
        # Test posting messages
        summary_channel = os.getenv('SUMMARY_CHANNEL')
        if summary_channel:
            print(f"\n📤 Testing posting to {summary_channel}...")
            try:
                await client.chat_postMessage(
                    channel=summary_channel,
                    text="🧪 Test message from Slack Summary Bot setup verification"
                )
                print(f"✅ Can post to {summary_channel}")
                print("   (You should see a test message in your summary channel)")
            except SlackApiError as e:
                print(f"❌ Cannot post to {summary_channel}: {e.response['error']}")
                print("   Make sure the bot is invited to this channel!")
                return False
        
        return True
        
    except SlackApiError as e:
        print(f"❌ Slack API error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🔍 Testing OpenAI connection...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def check_environment_variables():
    """Check all required environment variables."""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        'SLACK_BOT_TOKEN': 'Slack bot token',
        'OPENAI_API_KEY': 'OpenAI API key',
        'SUMMARY_CHANNEL': 'Channel for posting summaries'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if 'TOKEN' in var or 'KEY' in var:
                display_value = value[:10] + '...' + value[-4:] if len(value) > 14 else '***'
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set ({description})")
            all_present = False
    
    # Check optional variables
    print("\n📋 Optional variables:")
    ignore_channels = os.getenv('IGNORE_CHANNELS', '')
    if ignore_channels:
        print(f"✅ IGNORE_CHANNELS: {ignore_channels}")
    else:
        print("ℹ️  IGNORE_CHANNELS: Not set (will process all channels)")
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    print(f"ℹ️  LOG_LEVEL: {log_level}")
    
    return all_present

async def main():
    """Run all tests."""
    print("🚀 Slack Summary Bot Setup Verification")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    if not env_ok:
        print("\n⚠️  Please set all required environment variables in your .env file")
        sys.exit(1)
    
    # Test connections
    slack_ok = await test_slack_connection()
    openai_ok = await test_openai_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if slack_ok and openai_ok and env_ok:
        print("✅ All tests passed! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Run the bot manually: python slack_summary_bot.py")
        print("2. Set up scheduled execution (see docs/DEPLOYMENT.md)")
    else:
        print("❌ Some tests failed. Please fix the issues above before running the bot.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())