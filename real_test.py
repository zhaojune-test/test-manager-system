"""用真实API Key测试MiniMax"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
payload = {
    "model": "MiniMax-Text-01",
    "messages": [{"role": "user", "content": "你好，返回JSON：[{\"test\": \"ok\"}]"}],
    "max_tokens": 100
}

print("Testing MiniMax API with your API key...")
print(f"Key length: {len(API_KEY)}")

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, ensure_ascii=False)[:500]}")

    if 'choices' in result:
        content = result['choices'][0]['message']['content']
        print(f"\nSuccess! Content: {content}")
except Exception as e:
    print(f"Error: {e}")