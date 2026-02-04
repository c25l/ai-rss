"""Compatibility shim for older call sites.

This repo used to have an Azure AI Foundry-backed Claude client.
Azure interactions are being removed; this module now delegates to the
GitHub Copilot CLI wrapper in copilot.py.
"""

from copilot import Copilot


class Claude(object):
    """Backwards-compatible interface used by news/tech_news/daily_workflow."""

    def __init__(self, model: str | None = None, cli_command: str = "copilot"):
        self._client = Copilot(model=model, cli_command=cli_command)

    def warmup(self):
        return self._client.warmup()

    def generate(self, prompt, max_retries=10, base_delay=1.0):
        return self._client.generate(prompt, max_retries=max_retries, base_delay=base_delay)

    def rank_items(self, items, prompt_template, top_k=5, batch_size=10):
        return self._client.rank_items(items, prompt_template, top_k=top_k, batch_size=batch_size)

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
