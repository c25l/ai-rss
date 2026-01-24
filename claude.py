import os
import time
import random
import json
import re
from dotenv import load_dotenv
from anthropic import AnthropicFoundry

load_dotenv()


class Claude(object):
    """
    Azure AI Foundry client for Anthropic Claude models.
    Uses Anthropic API format with exponential backoff for rate limiting.
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_ENDPOINT", "https://chris-bonnell-1327-resource.services.ai.azure.com/anthropic/")
        self.api_key = os.getenv("AZURE_AI_API_KEY")
        self.model = os.getenv("AZURE_AI_DEPLOYMENT_NAME", "claude-sonnet-4-5")

        if not self.api_key:
            raise ValueError("AZURE_AI_API_KEY must be set in .env file")

    def warmup(self):
        """
        Warm up the model by sending a simple prompt to trigger loading.
        Call this at the start of a workflow to ensure the model is loaded.
        """
        print(f"Warming up Claude model: {self.model}")
        try:
            client = AnthropicFoundry(
                api_key=self.api_key,
                base_url=self.endpoint
            )
            client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}]
            )
            print("✓ Model loaded and ready")
            return True
        except Exception as e:
            print(f"✗ Model warmup failed: {e}")
            return False

    def generate(self, prompt, max_retries=10, base_delay=1.0):
        """
        Generate a response from Claude for the given prompt.

        Args:
            prompt: The prompt text to send to Claude
            max_retries: Maximum number of retries on failure
            base_delay: Base delay for exponential backoff

        Returns:
            String response from Claude
        """
        client = AnthropicFoundry(
            api_key=self.api_key,
            base_url=self.endpoint
        )
        try:
            message = client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": f"{prompt}"}
                ],
                max_tokens=4096,
                temperature=0.7,
            )
            return "\n\n".join([xx.text for xx in message.content])
        except Exception as e:
            if max_retries <= 0:
                raise
            delay = base_delay * 2 + random.uniform(0, 0.2)
            print(f"Exception: {e}, \n waiting {delay} then retrying")
            time.sleep(delay)
            return self.generate(prompt, max_retries=max_retries-1, base_delay=delay)

    def rank_items(self, items, prompt_template, top_k=5, batch_size=10):
        """
        Generic ranking method with batching: ranks items and returns indices of top_k selections.
        Uses recursive batching like research.py to handle large item counts efficiently.

        Args:
            items: List of items (articles, clusters, etc.) to rank (as formatted string)
            prompt_template: Custom prompt that will be formatted with item list
            top_k: Number of top items to select (default: 5)
            batch_size: Size of batches to process (default: 10)

        Returns:
            List of indices of top_k items, or all items if len(items) <= top_k
        """
        # Parse items string into list (split by newlines, filter [N] patterns)
        item_lines = [line for line in items.split('\n') if line.strip() and line.strip().startswith('[')]
        num_items = len(item_lines)

        if num_items <= top_k:
            return list(range(num_items))

        # If items fit in one batch, rank directly
        if num_items <= batch_size:
            return self._rank_single_batch(items, prompt_template, top_k, num_items)

        # Otherwise, use recursive batching
        return self._rank_batched(items, prompt_template, top_k, batch_size, num_items)

    def _rank_single_batch(self, items, prompt_template, top_k, num_items):
        """Rank a single batch of items"""
        # Format the prompt with items
        prompt = prompt_template.format(
            count=num_items,
            top_k=top_k,
            items=items
        )

        response = self.generate(prompt)

        # Parse the response to get indices
        try:
            # Extract JSON array from response
            match = re.search(r'\[[\d,\s]+\]', response)
            if match:
                selected_indices = json.loads(match.group())
                # Return valid indices only
                return [i for i in selected_indices if i < num_items][:top_k]
        except Exception as e:
            print(f"Error parsing ranking response: {e}")
            # Fallback to first top_k
            return list(range(min(top_k, num_items)))

        # Fallback to first top_k
        return list(range(min(top_k, num_items)))

    def _rank_batched(self, items, prompt_template, top_k, batch_size, num_items):
        """Recursively rank items in batches"""
        # Split items into batches
        item_lines = [line for line in items.split('\n') if line.strip() and line.strip().startswith('[')]

        current_indices = list(range(num_items))

        while len(current_indices) > top_k:
            # Process in batches
            new_indices = []

            for i in range(0, len(current_indices), batch_size):
                batch_indices = current_indices[i:i+batch_size]

                # Reformat items for this batch with renumbered indices
                batch_lines = []
                for new_idx, old_idx in enumerate(batch_indices):
                    # Replace old index with new index
                    old_line = item_lines[old_idx]
                    # Replace [old_idx] with [new_idx]
                    new_line = re.sub(r'^\[\d+\]', f'[{new_idx}]', old_line)
                    batch_lines.append(new_line)

                batch_items = '\n'.join(batch_lines)
                batch_top_k = min(top_k, len(batch_indices))

                # Rank this batch
                selected = self._rank_single_batch(batch_items, prompt_template, batch_top_k, len(batch_indices))

                # Map back to original indices
                new_indices.extend([batch_indices[idx] for idx in selected if idx < len(batch_indices)])

            # If we didn't reduce, break to avoid infinite loop
            if len(new_indices) >= len(current_indices):
                break

            current_indices = new_indices

        return current_indices[:top_k]


if __name__ == "__main__":
    xx = Claude()
    print(xx.generate("What's going on?"))
