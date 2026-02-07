"""Copilot LLM wrapper.

Mirrors the `Claude` class interface so callers can swap providers without
changing call sites.

Primary backend: GitHub Copilot CLI (`copilot -p ...`).
Default model: gpt-5.2 (can be overridden via COPILOT_MODEL env var or constructor param)
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import time
import tempfile


class Copilot:
    """Drop-in replacement for `Claude` with the same public methods.
    
    Uses GitHub Copilot CLI locally with gpt-5.2 by default.
    
    The model can be specified in three ways (in order of precedence):
    1. Constructor parameter: Copilot(model="gpt-5.2")
    2. Environment variable: COPILOT_MODEL=gpt-5.2
    3. Default: gpt-5.2
    
    Examples:
        # Use default gpt-5.2
        agent = Copilot()
        
        # Specify model explicitly
        agent = Copilot(model="gpt-4")
        
        # Use environment variable
        # export COPILOT_MODEL=gpt-5.2
        agent = Copilot()
    """

    def __init__(self, model: str | None = None, cli_command: str = "copilot"):
        # Default to gpt-5.2 if no model specified
        self.model = model or os.getenv("COPILOT_MODEL", "gpt-5.2")
        self.cli_command = cli_command

    def warmup(self):
        try:
            _ = self.generate("test", max_retries=1)
            return True
        except Exception:
            return False

    def _generate_via_cli(self, prompt: str, timeout_s: int = 120) -> str:
        # Avoid any CLI parsing/quoting issues by passing the prompt via @file.
        with tempfile.NamedTemporaryFile("w", delete=True, encoding="utf-8") as f:
            f.write(prompt)
            f.flush()
            cmd = [
                self.cli_command,
                "-p",
                f"@{f.name}",
                "-s",
                "--no-color",
                "--stream",
                "off",
                "--log-level",
                "error",
                "--no-ask-user",
                "--no-custom-instructions",
                "--disable-builtin-mcps",
            ]
            if self.model:
                cmd.extend(["--model", self.model])

            proc = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_s,
            )
            return self._clean_output(proc.stdout)

    @staticmethod
    def _clean_output(text: str) -> str:
        # In some versions the CLI prefixes responses with a leading bullet like "● ".
        text = text.strip("\n")
        if text.startswith("● ") or text.startswith("• "):
            text = text[2:]
        return text


    def generate(self, prompt, max_retries=10, base_delay=1.0):
        last_err = None
        delay = base_delay

        for _ in range(max_retries + 1):
            try:
                return self._generate_via_cli(str(prompt))
            except Exception as e:
                last_err = e
                time.sleep(delay + random.uniform(0, 0.2))
                delay = delay * 2

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

                selected = self._rank_single_batch(batch_items, prompt_template, batch_top_k, len(batch_indices))
                new_indices.extend([batch_indices[idx] for idx in selected if idx < len(batch_indices)])

            if len(new_indices) >= len(current_indices):
                break

            current_indices = new_indices

        return current_indices[:top_k]
