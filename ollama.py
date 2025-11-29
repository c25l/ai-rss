import requests
class Ollama(object):
    def __init__(self):
        self.model = 'qwen/qwen3-vl-4b'
        self.base_url = 'http://localhost:1234'

    def post_request(self, url: str, payload: dict):
        result = requests.post(url, json=payload)
        if result.status_code == 200:
            return result.json()
        else:
            return {"error": f"Request failed with status {result.status}"}

    def ollama(self, prompt: str, model: str = "qwen/qwen3-vl-4b", max_tokens: int = 4000, temp: float = 0) -> str:
        try:
            # LM Studio uses OpenAI-compatible API format
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temp,
                "top_p": 0.9,
                "stream": False
            }

            response = self.post_request(
                f"{self.base_url}/v1/completions",
                payload=payload
            )

            # OpenAI-compatible response format
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0].get("text", "").strip()
            else:
                content = ""

            # Split on </think> token and return only the part after
            content = content.split("</think>", 1)[-1].strip().split("...done thinking.")[-1].strip()

            return content

        except Exception as e:
            print(e)
            return ""

    def generate(self, prompt):
        return self.ollama(prompt, self.model)


if __name__=="__main__":
    xx =Ollama()
    print(xx.generate("hello"))
