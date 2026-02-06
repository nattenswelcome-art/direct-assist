import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

TOKEN = os.getenv("YANDEX_TOKEN")
CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
LOGIN = os.getenv("YANDEX_LOGIN")

def test_v5():
    url = "https://api.direct.yandex.com/json/v5/campaigns"
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "Client-Login": LOGIN,
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    body = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name"],
            "Page": {"Limit": 3}
        }
    }
    
    print(f"Testing V5 API for Login: {LOGIN}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Token: {TOKEN[:5]}...{TOKEN[-5:]}")
    
    try:
        resp = requests.post(url, headers=headers, json=body)
        print(f"Status Code: {resp.status_code}")
        
        try:
            data = resp.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print("Response Text:", resp.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_v5()
