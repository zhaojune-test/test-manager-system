"""测试MiniMax生成简洁JSON"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 简化版 prompt - 只要求返回2个测试用例
payload = {
    "model": "minimax-m2.7",
    "messages": [
        {"role": "system", "content": "你是一个测试工程师。直接返回JSON数组，不要任何其他内容。格式：[{\"case_id\":\"TC_001\",\"name\":\"测试1\",\"type\":\"functional\",\"priority\":\"high\"}]"},
        {"role": "user", "content": "为用户登录功能生成2个测试用例"}
    ],
    "max_tokens": 500
}

print("Testing simple JSON generation...")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    result = resp.json()
    print(f"Status: {resp.status_code}")

    if result.get('choices'):
        content = result['choices'][0]['message']['content']
        print(f"\nContent:\n{content}\n")

        # Try to parse as JSON
        try:
            data = json.loads(content)
            print(f"[OK] Parsed as JSON: {len(data)} items")
        except json.JSONDecodeError as e:
            print(f"[X] JSON parse error: {e}")
            # Try to find JSON array manually
            if '[' in content and ']' in content:
                start = content.find('[')
                end = content.rfind(']') + 1
                try:
                    data = json.loads(content[start:end])
                    print(f"[OK] Extracted JSON array: {len(data)} items")
                except:
                    print("[X] Could not extract JSON array")
    elif result.get('base_resp'):
        print(f"Error: {result['base_resp']}")
except Exception as e:
    print(f"Error: {e}")