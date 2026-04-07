import requests
import json

url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

response = requests.get(url)
data = response.json()

with open("games.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("✅ Updated games.json with latest game list.")
