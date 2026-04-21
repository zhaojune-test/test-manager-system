"""直接测试MiniMax API"""
import os
import sys
import json
import requests

# MiniMax API配置
API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
API_KEY = os.environ.get("MINIMAX_API_KEY", "") or "sk-cp-cMEb6T2Rkx3xxx"  # 使用一个测试key

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "MiniMax-Text-01",
    "messages": [
        {"role": "system", "content": "你是一个测试工程师，擅长生成测试用例。直接返回JSON数组格式的测试用例，不要任何额外文字。"},
        {"role": "user", "content": "请为用户登录功能生成2个测试用例，格式如：[{\"case_id\": \"TC_001\", \"name\": \"测试名称\", \"type\": \"functional\", \"description\": \"描述\", \"priority\": \"high\", \"steps\": [{\"action\": \"操作\", \"expected\": \"预期\"}], \"expected_result\": \"结果\"}]"}
    ],
    "temperature": 0.7,
    "max_tokens": 4096
}

print("正在调用MiniMax API...")
print(f"API URL: {API_URL}")
print(f"API Key: {API_KEY[:10]}...")

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    print(f"\nHTTP Status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")

    result = response.json()
    print(f"\nResult keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
    print(f"Result: {json.dumps(result, ensure_ascii=False)[:1000]}")

    if 'error' in result:
        print(f"\nAPI Error: {result['error']}")
    else:
        choices = result.get('choices')
        print(f"\nChoices: {choices}")
        if choices and len(choices) > 0:
            content = choices[0].get('message', {}).get('content', '')
            print(f"\nContent: {content}")
        else:
            print("\nNo choices in response!")

except Exception as e:
    print(f"\nException: {e}")
    import traceback
    traceback.print_exc()