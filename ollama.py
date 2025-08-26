import requests
class Ollama(object):
    def __init__(self):
        self.model = 'qwen3:8b'

    def post_request(self, url: str, payload: dict):
        result = requests.post(url, json=payload)
        if result.status_code == 200:
            return result.json()
        else:
            return {"error": f"Request failed with status {result.status}"}

    def ollama(self, prompt: str, model: str = "qwen3:8b", max_tokens: int = 4000, temp: float = 0) -> str:
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "max_tokens": max_tokens,
                    "top_p": 0.9
                }
            }
            
            response =  self.post_request(
                "http://localhost:11434/api/generate", 
                payload=payload
            )
            content = response.get("response", "").strip()        
            
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
