from google import genai

client = genai.Client(api_key="AIzaSyCsEc9Ad8dMmCSVN129UfE9GNT6ysk1A90")

print("Available models:")
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(f"- {model.name}")
