import os
import requests
import time
import random
from dotenv import load_dotenv
from anthropic import AnthropicFoundry
load_dotenv()

class Claude(object):
    """
    Azure AI Foundry client for Anthropic Claude models.
    Uses OpenAI-compatible API format with exponential backoff for rate limiting.
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_ENDPOINT", "https://chris-bonnell-1327-resource.services.ai.azure.com/openai/v1/")
        self.api_key = os.getenv("AZURE_AI_API_KEY")
        # Default to Claude Sonnet 4.5 - update AZURE_AI_DEPLOYMENT_NAME in .env if your deployment has a different name
        self.deployment_name = os.getenv("AZURE_AI_DEPLOYMENT_NAME", "claude-sonnet-4-5")

        if not self.api_key:
            raise ValueError("AZURE_AI_API_KEY must be set in .env file")

    def generate(self, prompt, max_retries=10, base_delay=1.0):
        client = AnthropicFoundry(
            api_key=self.api_key,
            base_url=self.endpoint
        )
        try:
            message = client.messages.create(
                model=self.deployment_name,
                messages=[
                    {"role": "user", "content": f"{prompt}"}
                ],
                max_tokens=1024,
                )
            return "\n\n".join([xx.text for xx in message.content])
        except Exception as e:
            delay = base_delay * 2  + random.uniform(0, 0.2)
            print(f"Exception: {e[:300] + e[-300:]}, \n waiting {delay} then retrying")
            time.sleep(delay)
        return self.generate(prompt, max_retries=max_retries-1,base_delay=delay)

if __name__=="__main__":
    xx=Claude()
    print(xx.generate("Whats going on?"))
