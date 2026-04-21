"""测试minimax-m2.7生成测试用例"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "minimax-m2.7",
    "messages": [
        {"role": "system", "content": "你是一个测试工程师，擅长生成测试用例。直接返回JSON数组格式的测试用例，不要任何额外文字。"},
        {"role": "user", "content": "请为用户登录功能生成2个测试用例，格式如：[{\"case_id\": \"TC_001\", \"name\": \"测试名称\", \"type\": \"functional\", \"description\": \"描述\", \"priority\": \"high\", \"steps\": [{\"action\": \"操作\", \"expected\": \"预期\"}], \"expected_result\": \"结果\"}]"}
    ],
    "max_tokens": 1000
}

print("Testing test case generation with minimax-m2.7...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response keys: {result.keys()}")
    print(f"Response: {json.dumps(result, ensure_ascii=False)[:800]}")

    if result.get('choices'):
        content = result['choices'][0]['message']['content']
        print(f"\n[OK] Success! Content:\n{content}")
    elif result.get('base_resp'):
        print(f"\n[X] Error: {result['base_resp']}")
except Exception as e:
    print(f"Error: {e}")