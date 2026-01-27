#!/usr/bin/env python3
"""Manual test script to simulate Slack events and webhook calls.

Usage:
    # Test health check
    python scripts/test_relay.py health

    # Test webhook relay
    python scripts/test_relay.py webhook "Your test message"

    # Test simulated DM (sends directly to Slack channel, bypassing bot)
    python scripts/test_relay.py dm "Your test message"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv


def test_health(base_url: str) -> bool:
    """Test the health check endpoint."""
    url = f"{base_url}/health"
    print(f"Testing health check: {url}")

    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False


def test_webhook(base_url: str, message: str, api_key: str) -> bool:
    """Test the webhook endpoint."""
    url = f"{base_url}/webhook"
    print(f"Testing webhook: {url}")

    payload = {
        "message": message,
        "source": "test_relay.py",
        "timestamp": datetime.now().isoformat(),
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False


def test_dm_direct(message: str, channel_id: str, bot_token: str) -> bool:
    """Send a test message directly to Slack channel (simulating relay output)."""
    url = "https://slack.com/api/chat.postMessage"
    print(f"Sending test message directly to channel: {channel_id}")

    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "channel": channel_id,
        "text": f"*Test Message*\n\n{message}\n\n_Sent via test_relay.py_",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: ok={data.get('ok')}, error={data.get('error', 'none')}")
        return data.get("ok", False)
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False


def main() -> int:
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test LabSlack bot endpoints")
    parser.add_argument(
        "test_type",
        choices=["health", "webhook", "dm"],
        help="Type of test to run",
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="Test message from test_relay.py",
        help="Message to send (for webhook/dm tests)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:3000",
        help="Base URL of the bot (default: http://localhost:3000)",
    )

    args = parser.parse_args()

    if args.test_type == "health":
        success = test_health(args.url)

    elif args.test_type == "webhook":
        api_key = os.getenv("WEBHOOK_API_KEY")
        if not api_key:
            print("Error: WEBHOOK_API_KEY not set in environment")
            return 1
        success = test_webhook(args.url, args.message, api_key)

    elif args.test_type == "dm":
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        channel_id = os.getenv("RELAY_CHANNEL_ID")
        if not bot_token or not channel_id:
            print("Error: SLACK_BOT_TOKEN and RELAY_CHANNEL_ID must be set")
            return 1
        success = test_dm_direct(args.message, channel_id, bot_token)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
