"""测试M2模型变体"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

models = [
    "minmax-m2.7",
    "minimax-m2.7",
    "minmax_m2.7",
    "minimax_m2.7",
    "minmax-m2",
    "minimax-m2",
    "minimax",
    "MM-Text-01",
    "mmtext-01",
]

for model in models:
    print(f"\nTesting: {model}", flush=True)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        result = resp.json()
        if result.get('choices'):
            print(f"  [OK]", flush=True)
        elif result.get('base_resp'):
            err = result['base_resp'].get('status_msg', 'unknown')[:60]
            print(f"  [X] {err}", flush=True)
        else:
            print(f"  [?] {str(result)[:60]}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)