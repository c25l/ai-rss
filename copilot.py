from __future__ import annotations

import json
import os
import random
import re
import subprocess
import time
import tempfile
from typing import List, Union


class Copilot:
    """LLM wrapper supporting Azure OpenAI and GitHub Copilot CLI.

    Mode priority:
    1. Azure OpenAI — when AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set
    2. GitHub Copilot CLI — fallback

    The completion model can be specified via:
    - Constructor parameter: Copilot(model="claude-opus-4.6")
    - Environment variable: COPILOT_MODEL (CLI) or AZURE_OPENAI_DEPLOYMENT (Azure)
    - Default: claude-opus-4.6 (CLI)

    Embedding support (Azure only):
    - Requires AZURE_OPENAI_EMBEDDING_DEPLOYMENT env var
    """

    def __init__(self, model: str | None = None, cli_command: str = "/usr/local/bin/copilot"):
        self.cli_command = cli_command
        self._azure_client = None

        # Detect Azure OpenAI availability
        self._azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self._azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self._azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self._azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self._azure_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        self.use_azure = bool(self._azure_endpoint and self._azure_api_key and self._azure_deployment)

        if self.use_azure:
            self.model = model or self._azure_deployment
        else:
            self.model = model or os.getenv("COPILOT_MODEL", "claude-opus-4.6")

    def warmup(self):
        try:
            _ = self.generate("test", max_retries=1)
            return True
        except Exception:
            return False

    def _get_azure_client(self):
        """Lazily initialize the Azure OpenAI client."""
        if self._azure_client is None:
            from openai import AzureOpenAI
            self._azure_client = AzureOpenAI(
                azure_endpoint=self._azure_endpoint,
                api_key=self._azure_api_key,
                api_version=self._azure_api_version,
            )
        return self._azure_client

    def _generate_via_azure(self, prompt: str, timeout_s: int = 300) -> str:
        """Generate a completion using Azure OpenAI."""
        client = self._get_azure_client()
        response = client.chat.completions.create(
            model=self._azure_deployment,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout_s,
        )
        return (response.choices[0].message.content or "").strip()

    def embed(self, texts: Union[str, List[str]], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings using Azure OpenAI.

        Args:
            texts: Single string or list of strings to embed.
            batch_size: Number of texts per API call.

        Returns:
            List of embedding vectors (one per input text).

        Raises:
            RuntimeError: If Azure embeddings are not configured.
        """
        if not self.use_azure or not self._azure_embedding_deployment:
            raise RuntimeError(
                "Azure OpenAI embedding deployment not configured. "
                "Set AZURE_OPENAI_EMBEDDING_DEPLOYMENT env var."
            )

        if isinstance(texts, str):
            texts = [texts]

        client = self._get_azure_client()
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = client.embeddings.create(
                model=self._azure_embedding_deployment,
                input=batch,
            )
            # Sort by index to preserve order
            sorted_data = sorted(response.data, key=lambda d: d.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

        return all_embeddings

    def has_embeddings(self) -> bool:
        """Check if embedding support is available."""
        return self.use_azure and bool(self._azure_embedding_deployment)

    def _generate_via_cli(self, prompt: str, timeout_s: int = 300) -> str:
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
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_s,
            )
            return self._clean_output(proc.stdout)

    @staticmethod
    def _clean_output(text: str) -> str:
        """Clean Copilot CLI output to extract just the generated content.
        
        Strategy: Find "Daily Briefing" and discard everything before it.
        This is more robust than trying to match every possible preamble pattern.
        """
        text = text.strip()
        
        # Find the line containing "Daily Briefing" - this is where content starts
        lines = text.split('\n')
        content_start_idx = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Remove bullet prefix if present to check content
            if stripped.startswith("● ") or stripped.startswith("• "):
                stripped = stripped[2:].strip()
            
            # Found "Daily Briefing" - this is where real content starts
            if "Daily Briefing" in stripped:
                content_start_idx = i
                break
        
        # If we didn't find "Daily Briefing", return cleaned text as-is
        if content_start_idx is None:
            # Just remove bullets from start
            while text.startswith("● ") or text.startswith("• "):
                text = text[2:].strip()
            return text
        
        # Extract content from "Daily Briefing" onward
        content_lines = []
        for i in range(content_start_idx, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            # Remove bullet prefix if present
            if stripped.startswith("● ") or stripped.startswith("• "):
                stripped = stripped[2:].strip()
                content_lines.append(stripped)
            else:
                content_lines.append(line.rstrip())
        
        result = '\n'.join(content_lines).strip()
        
        # Ensure the Daily Briefing line has proper markdown heading
        if result.startswith("Daily Briefing - ") and not result.startswith("# Daily Briefing"):
            result = "# " + result
        
        return result


    def generate(self, prompt, max_retries=10, base_delay=1.0):
        last_err = None
        delay = base_delay
        print(f"generating from {prompt[0:200]}")

        for attempt in range(max_retries + 1):
            try:
                if self.use_azure:
                    return self._generate_via_azure(str(prompt))
                return self._generate_via_cli(str(prompt))
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
                last_err = e
                if attempt < max_retries:
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
