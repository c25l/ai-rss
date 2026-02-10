# LLM Configuration Guide

h3lper uses the **GitHub Copilot CLI** for all LLM calls.

## Prerequisites

Install the GitHub Copilot CLI:

```bash
which copilot
# Should show: /usr/local/bin/copilot (or similar)
```

## Configuration

Set your preferred model via the `COPILOT_MODEL` environment variable in `.env`:

```bash
COPILOT_MODEL=claude-opus-4.6
```

Default model: `claude-opus-4.6`

## Testing

```bash
python3 -c "
from copilot import Copilot
c = Copilot()
print(f'Model: {c.model}')
print('Testing generation...')
print(c.generate('Say hello in one word.'))
"
```

## Troubleshooting

### Hanging during generation

**Symptoms:** Prints "generating from..." and then hangs.

**Cause:** CLI not closing stdin. Fixed by `stdin=subprocess.DEVNULL` in the subprocess call.

### CLI not found

**Symptoms:** Errors about `/usr/local/bin/copilot` not being found.

**Solution:** Install the GitHub Copilot CLI.
