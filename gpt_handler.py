import requests
import json


class GPTHandler:
    def __init__(self, api_key, api_url="https://api.openai-proxy.org/v1/chat/completions"):
        self.api_key = api_key
        self.api_url = api_url

    def chat_with_gpt(self, prompt):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()

            return response.json()['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            return f"Network Error: {e}"
        except (KeyError, IndexError) as e:
            return f"Response Parse Error: {e}"