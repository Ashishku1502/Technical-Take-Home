import urllib.request
import json

try:
    print("Checking server status...")
    url = "http://127.0.0.1:8000/api/orders/summary/?limit=5"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Server Response (Success):")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error connecting to server: {e}")
