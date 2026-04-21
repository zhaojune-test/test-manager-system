"""测试JSON解析"""
import json

# 模拟MiniMax返回的内容
content = '''```json
[
  {
    "case_id": "TC_001",
    "name": "测试1",
    "type": "functional",
    "description": "描述",
    "priority": "high",
    "steps": [
      {"action": "操作", "expected": "预期"}
    ],
    "expected_result": "结果",
    "tags": ["标签"]
  }
]
```', 'role': 'assistant', 'name': 'MiniMax AI'
'''

print(f"Content length: {len(content)}")
print(f"Content ends with: ...{content[-100:]}")

# 尝试提取JSON
json_str = content.strip()

# 移除 fences
fences_to_try = ['```json', '```JSON', '```', '```json\n', '```\n']
for fence in fences_to_try:
    if json_str.startswith(fence):
        json_str = json_str[len(fence):].strip()
        print(f"Stripped prefix '{fence}', now starts with: {json_str[:50]}")

# Find JSON array bounds
json_start = json_str.find('[')
json_end = json_str.rfind(']') + 1

print(f"json_start: {json_start}, json_end: {json_end}")

if json_start >= 0 and json_end > json_start:
    extracted = json_str[json_start:json_end]
    print(f"Extracted JSON: {extracted[:100]}...")
    try:
        data = json.loads(extracted)
        print(f"SUCCESS: Parsed {len(data)} items")
    except json.JSONDecodeError as e:
        print(f"FAILED: {e}")
else:
    print("Could not find JSON bounds")