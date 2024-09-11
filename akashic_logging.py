import requests
import json


def log_info(message: str, level: str = "INFO") -> str | None:
    url = "http://localhost:5231/post"
    payload = {"level": level, "message": message, "name": "stock-tui"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return None
