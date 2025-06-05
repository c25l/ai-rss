import requests
import json
import ollama 

def generate(prompt):
    prompt = f"{prompt}\n\n\\no_think"
    resp = ollama.generate("qwen3:0.6b", prompt, stream=False)
    print(resp)
    print(dir(resp))
    return resp.response.split("</think>")[-1].strip()

def parse(response):
    lines = response.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1]
    if lines[-1].endswith("```"):
        lines = lines[:-1]
    return json.reads("\n".join(lines))
