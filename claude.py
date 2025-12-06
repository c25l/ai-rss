import subprocess
class Claude(object):
    def generate(self, prompt):
        try:
            result = subprocess.run(
                ["/home/chris/.local/bin/claude", "--tools", "\"\"","-p", prompt],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Error calling Claude: {e}")
            return ""


if __name__=="__main__":
    xx=Claude()
    print(xx.generate("Whats going on?"))
