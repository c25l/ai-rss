import json
import os
import random
import re
import time

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

load_dotenv()


class Claude(object):
    """Azure AI Foundry client for Anthropic Claude models."""

    def __init__(self):
        self.endpoint = os.getenv(
            "AZURE_AI_ENDPOINT",
            "https://chris-bonnell-1327-resource.services.ai.azure.com/openai/v1/",
        )
        self.api_key = os.getenv("AZURE_AI_API_KEY")
        self.deployment_name = os.getenv("AZURE_AI_DEPLOYMENT_NAME", "claude-sonnet-4-5")

        if not self.api_key:
            raise ValueError("AZURE_AI_API_KEY must be set in .env file")

        self._client = AnthropicFoundry(api_key=self.api_key, base_url=self.endpoint)

    def warmup(self):
        try:
            _ = self.generate("test", max_retries=1)
            return True
        except Exception:
            return False

    def generate(self, prompt, max_retries=10, base_delay=1.0):
        delay = base_delay
        last_err = None

        for _ in range(max_retries + 1):
            try:
                message = self._client.messages.create(
                    model=self.deployment_name,
                    messages=[{"role": "user", "content": f"{prompt}"}],
                    max_tokens=1024,
                )
                return "\n\n".join([xx.text for xx in message.content])
            except Exception as e:
                last_err = e
                msg = str(e)
                delay = delay * 2 + random.uniform(0, 0.2)
                print(f"Exception: {msg[:300]}, \n waiting {delay} then retrying")
                time.sleep(delay)

        raise last_err

    def rank_items(self, items, prompt_template, top_k=5, batch_size=10):
        item_lines = [line for line in items.split("\n") if line.strip() and line.strip().startswith("[")]
        num_items = len(item_lines)

        if num_items <= top_k:
            return list(range(num_items))

        if num_items <= batch_size:
            return self._rank_single_batch(items, prompt_template, top_k, num_items)

        return self._rank_batched(items, prompt_template, top_k, batch_size, num_items)

    def _rank_single_batch(self, items, prompt_template, top_k, num_items):
        prompt = prompt_template.format(count=num_items, top_k=top_k, items=items)
        response = self.generate(prompt)

        try:
            match = re.search(r"\[[\d,\s]+\]", response)
            if match:
                selected_indices = json.loads(match.group())
                return [i for i in selected_indices if i < num_items][:top_k]
        except Exception:
            return list(range(min(top_k, num_items)))

        return list(range(min(top_k, num_items)))

    def _rank_batched(self, items, prompt_template, top_k, batch_size, num_items):
        item_lines = [line for line in items.split("\n") if line.strip() and line.strip().startswith("[")]
        current_indices = list(range(num_items))

        while len(current_indices) > top_k:
            new_indices = []

            for i in range(0, len(current_indices), batch_size):
                batch_indices = current_indices[i : i + batch_size]

                batch_lines = []
                for new_idx, old_idx in enumerate(batch_indices):
                    old_line = item_lines[old_idx]
                    new_line = re.sub(r"^\[\d+\]", f"[{new_idx}]", old_line)
                    batch_lines.append(new_line)

                batch_items = "\n".join(batch_lines)
                batch_top_k = min(top_k, len(batch_indices))

                selected = self._rank_single_batch(
                    batch_items, prompt_template, batch_top_k, len(batch_indices)
                )
                new_indices.extend(
                    [batch_indices[idx] for idx in selected if idx < len(batch_indices)]
                )

            if len(new_indices) >= len(current_indices):
                break

            current_indices = new_indices

        return current_indices[:top_k]


if __name__ == "__main__":
    xx = Claude()
    print(xx.generate("Whats going on?"))
