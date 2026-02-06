import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("YANDEX_TOKEN")
LOGIN = os.getenv("YANDEX_LOGIN")
URL = "https://api.direct.yandex.com/v4/json/"

async def test():
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    
    # Payload for GetClientInfo
    payload = {
        "method": "GetClientInfo",
        "token": TOKEN,
        "param": [LOGIN],
        "locale": "ru"
    }
    
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    
    print(f"Sending request to {URL}...")
    print(f"Login: {LOGIN}")
    print(f"Token: {TOKEN[:5]}...{TOKEN[-5:]}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, data=data, headers=headers) as resp:
            print(f"Status Code: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test())
