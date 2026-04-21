"""测试abab6.5s-chat模型"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
payload = {
    "model": "abab6.5s-chat",
    "messages": [{"role": "user", "content": "返回JSON格式：[{\"case_id\": \"TC_001\", \"name\": \"测试登录\", \"type\": \"functional\"}]"}],
    "max_tokens": 200
}

print("Testing abab6.5s-chat model...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, ensure_ascii=False)[:500]}")

    if result.get('choices'):
        content = result['choices'][0]['message']['content']
        print(f"\nSuccess! Content: {content}")
    elif result.get('base_resp'):
        print(f"\nError: {result['base_resp']}")
except Exception as e:
    print(f"Error: {e}")