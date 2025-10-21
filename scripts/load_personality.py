import json, os

p = os.path.expanduser("Mainmi/config/personality.json")

with open(p, "r", encoding="utf-8") as f:

    personality = json.load(f)

print(personality["meta"]["name"], "loaded. Key traits:", personality["personality"]["archetype"])

