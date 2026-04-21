"""测试不同模型"""
import requests
import json
import sys

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

models_to_test = [
    "MiniMax-Text-01",
    "abab6.5s-chat",
    "abab5.5-chat",
    "abab-chat",
]

for model in models_to_test:
    print(f"\nTesting model: {model}", flush=True)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        result = resp.json()
        if result.get('choices'):
            msg = result['choices'][0].get('message', {})
            content = msg.get('content', 'N/A')[:50] if msg else 'N/A'
            print(f"  [OK] Supported! Response: {content}", flush=True)
        elif result.get('base_resp'):
            err_msg = result['base_resp'].get('status_msg', 'unknown')
            print(f"  [X] Not supported: {err_msg}", flush=True)
        else:
            print(f"  [?] Other: {str(result)[:100]}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)