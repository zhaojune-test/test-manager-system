"""详细调试JSON解析"""
import requests
import json

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 使用之前成功的简化prompt
payload = {
    "model": "minimax-m2.7",
    "messages": [
        {"role": "system", "content": "你是一个测试工程师。直接返回JSON数组，不要任何其他内容。格式：[{\"case_id\":\"TC_001\",\"name\":\"测试1\",\"type\":\"functional\",\"priority\":\"high\"}]"},
        {"role": "user", "content": "为用户登录功能生成2个测试用例"}
    ],
    "max_tokens": 500
}

print("Sending request...")
resp = requests.post(url, headers=headers, json=payload, timeout=30)
result = resp.json()

if result.get('choices'):
    content = result['choices'][0]['message']['content']
    print(f"\nRaw content length: {len(content)}")
    print(f"Raw content ends (last 150 chars): {repr(content[-150:])}")

    # 应用解析逻辑
    json_str = content.strip()

    # 移除 fences
    for fence in ['```json', '```JSON', '```', '```json\n', '```\n']:
        if json_str.startswith(fence):
            json_str = json_str[len(fence):].strip()
            print(f"After stripping fence '{fence}': starts with {repr(json_str[:50])}")

    # 找到JSON数组
    json_start = json_str.find('[')
    json_end = json_str.rfind(']') + 1

    print(f"json_start={json_start}, json_end={json_end}")

    if json_start >= 0 and json_end > json_start:
        extracted = json_str[json_start:json_end]
        print(f"Extracted length: {len(extracted)}")
        print(f"Extracted ends (last 100 chars): {repr(extracted[-100:])}")

        try:
            data = json.loads(extracted)
            print(f"SUCCESS: Parsed {len(data)} items")
            print(f"First item: {data[0]}")
        except json.JSONDecodeError as e:
            print(f"FAILED to parse: {e}")
            # 显示解析失败的位置附近的字符
            pos = e.pos if hasattr(e, 'pos') else 0
            print(f"Error near position {pos}:")
            print(f"  ...{repr(extracted[max(0,pos-30):pos+30])}...")
else:
    print(f"Error: {result.get('base_resp')}")