import requests
import json

def generate(prompt, model="qwen3:8b", max_tokens=4000):
    """Generate text using Ollama server"""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "top_p": 0.9
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        
        result = response.json()
        content = result.get("response", "").strip()
        
        # Split on </think> token and return only the part after
        if "</think>" in content:
            content = content.split("</think>", 1)[1].strip()
        
        return content
        
    except requests.exceptions.Timeout:
        print("Ollama request timed out")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"Ollama API error: {e}")
        return ""
    except Exception as e:
        print(f"Generation error: {e}")
        return ""

def parse(response):
    lines = response.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines[-1].endswith("```"):
        lines = lines[:-1]
    return json.loads("\n".join(lines))
