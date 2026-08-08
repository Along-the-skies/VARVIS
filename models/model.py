import requests
import json

from core.config import load_api_key


# =========================
# Configuration
# =========================

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


# =========================
# AI Request
# =========================

def ask_ai(prompt):

    api_key = load_api_key()

    print("API KEY EXISTS:", bool(api_key))

    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:

        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=60
        )

        print("STATUS:", response.status_code)

        return response

    except requests.RequestException as e:

        print("REQUEST ERROR:", e)

        return None


# =========================
# Response Handling
# =========================

def parse_response(response):

    if response is None:

        return {
            "type": "chat",
            "content": "I couldn't connect to the AI service, Sir."
        }

    try:
        data = response.json()

    except ValueError:

        return {
            "type": "chat",
            "content": "The AI service returned an invalid response, Sir."
        }

    if "error" in data:

        error = data["error"]

        if isinstance(error, dict):
            message = error.get(
                "message",
                "Unknown AI error"
            )
        else:
            message = str(error)

        return {
            "type": "chat",
            "content": f"AI error: {message}"
        }

    if "choices" not in data:

        return {
            "type": "chat",
            "content": "I couldn't get a valid response from the AI service, Sir."
        }

    if not data["choices"]:

        return {
            "type": "chat",
            "content": "The AI returned an empty response, Sir."
        }

    try:

        content = data["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError):

        return {
            "type": "chat",
            "content": "The AI response format was unexpected, Sir."
        }

    try:

        return json.loads(content)

    except json.JSONDecodeError:

        return {
            "type": "chat",
            "content": content
        }


# =========================
# Command Understanding
# =========================

def understand_command(command):

    prompt = f"""
You are VARVIS or Jarvis, a personal desktop AI assistant.

Address the user as "Sir".
Be friendly, concise, confident and slightly witty.

If the user requests a computer action, return:

{{
    "type": "command",
    "content": "normalized command"
}}

Supported commands:

open <app>
close <app>

check cpu
check ram
check battery
check disk
check uptime
check temp

change <setting> <value>

If the user is having normal conversation, return:

{{
    "type": "chat",
    "content": "friendly response"
}}

Return ONLY valid JSON.

USER REQUEST:
{command}
"""

    response = ask_ai(prompt)

    return parse_response(response)