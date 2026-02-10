from __future__ import annotations

import json
import os
import random
import re
import subprocess
import time
import tempfile

# Try to import OpenAI SDK (for Azure OpenAI)
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class Copilot:
    """Drop-in replacement for `Claude` with the same public methods.
    
    Supports three modes of operation (in priority order):
    1. Azure OpenAI (preferred): Uses Azure OpenAI configuration from .env
    2. Anthropic API: Uses ANTHROPIC_API_KEY from .env
    3. GitHub Copilot CLI (fallback): Uses local CLI
    
    The mode is determined automatically based on environment configuration.
    
    Azure OpenAI Configuration:
        AZURE_OPENAI_ENDPOINT - Your Azure OpenAI endpoint
        AZURE_OPENAI_API_KEY - Your Azure OpenAI API key
        AZURE_OPENAI_DEPLOYMENT - Your deployment name
        AZURE_OPENAI_API_VERSION - API version (default: 2024-02-15-preview)
    
    The model can be specified via:
    1. Constructor parameter: Copilot(model="gpt-4")
    2. Environment variable: COPILOT_MODEL=gpt-4
    3. Azure deployment name (for Azure mode)
    4. Default: deployment name (Azure), claude-3-5-sonnet-20241022 (Anthropic), claude-opus-4.6 (CLI)
    
    Examples:
        # Use Azure OpenAI (if configured)
        agent = Copilot()
        
        # Specify model explicitly
        agent = Copilot(model="gpt-4")
        
        # Use environment variables
        # export AZURE_OPENAI_ENDPOINT=https://...
        # export AZURE_OPENAI_API_KEY=...
        # export AZURE_OPENAI_DEPLOYMENT=gpt-4
        agent = Copilot()
    """

    def __init__(self, model: str | None = None, cli_command: str = "/usr/local/bin/copilot"):
        # Check for Azure OpenAI configuration (highest priority)
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        self.use_azure = azure_endpoint and azure_key and azure_deployment and OPENAI_AVAILABLE
        self.use_anthropic = False
        self.azure_client = None
        self.anthropic_client = None
        
        if self.use_azure:
            # Azure OpenAI mode
            self.azure_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version=azure_api_version
            )
            self.azure_deployment = azure_deployment
            # Use deployment name as model, or override
            self.model = model or os.getenv("COPILOT_MODEL", azure_deployment)
            self.mode = "azure"
        else:
            # Check for Anthropic API key (second priority)
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            self.use_anthropic = anthropic_key and ANTHROPIC_AVAILABLE
            
            if self.use_anthropic:
                # Anthropic API mode
                self.anthropic_client = Anthropic(api_key=anthropic_key)
                self.model = model or os.getenv("COPILOT_MODEL", "claude-3-5-sonnet-20241022")
                self.mode = "anthropic"
            else:
                # CLI mode (fallback)
                self.model = model or os.getenv("COPILOT_MODEL", "claude-opus-4.6")
                self.mode = "cli"
            
        self.cli_command = cli_command

    def warmup(self):
        try:
            _ = self.generate("test", max_retries=1)
            return True
        except Exception:
            return False

    def _generate_via_azure(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using Azure OpenAI."""
        if not self.azure_client:
            raise ValueError("Azure OpenAI client not initialized")
        
        response = self.azure_client.chat.completions.create(
            model=self.azure_deployment,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        # Extract text from response
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content or ""
        return ""

    def _generate_via_anthropic(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        message = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract text from response
        if message.content and len(message.content) > 0:
            return message.content[0].text
        return ""

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
                # Try modes in priority order
                if self.use_azure:
                    # Try Azure OpenAI first
                    return self._generate_via_azure(str(prompt))
                elif self.use_anthropic:
                    # Try Anthropic API
                    return self._generate_via_anthropic(str(prompt))
                else:
                    # Use CLI
                    return self._generate_via_cli(str(prompt))
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries + 1} failed ({self.mode} mode): {str(e)}")
                last_err = e
                
                # On first failure, try fallback modes
                if attempt == 0:
                    # Try fallback chain: Azure → Anthropic → CLI
                    if self.use_azure:
                        # Azure failed, try Anthropic
                        if self.use_anthropic or (os.getenv("ANTHROPIC_API_KEY") and ANTHROPIC_AVAILABLE):
                            print("Azure OpenAI failed, trying Anthropic API fallback...")
                            try:
                                if not self.anthropic_client and ANTHROPIC_AVAILABLE:
                                    self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                                return self._generate_via_anthropic(str(prompt))
                            except Exception as anthropic_err:
                                print(f"Anthropic fallback failed: {str(anthropic_err)}")
                        
                        # Try CLI as last resort
                        print("Trying CLI fallback...")
                        try:
                            return self._generate_via_cli(str(prompt))
                        except Exception as cli_err:
                            print(f"CLI fallback also failed: {str(cli_err)}")
                            last_err = cli_err
                    
                    elif self.use_anthropic:
                        # Anthropic failed, try CLI
                        print("Anthropic API failed, trying CLI fallback...")
                        try:
                            return self._generate_via_cli(str(prompt))
                        except Exception as cli_err:
                            print(f"CLI fallback also failed: {str(cli_err)}")
                            last_err = cli_err
                
                # Exponential backoff before retry
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
