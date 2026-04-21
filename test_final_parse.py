"""测试最终解析"""
import json

# 从debug输出重建实际内容
content = '''```json
[
  {
    "case_id": "TC_LOGIN_001",
    "name": "��ȷ�û����������¼�ɹ�",
    "type": "functional",
    "description": "��֤�û�ʹ����ȷ���û����������ܹ��ɹ���¼ϵͳ",
    "priority": "high",
    "steps": [
      {"action": "������ȷ���û���", "expected": "�û�����ȷ��ʾ"},
      {"action": "������ȷ������", "expected": "������ʾΪ���ܷ���"},
      {"action": "�����¼��ť", "expected": "ҳ����ת��ϵͳ��ҳ"}
    ],
    "expected_result": "��¼�ɹ�����ʾ�û�������Ϣ��ϵͳ������",
    "tags": ["��¼", "���Ĺ���", "����"]
  },
  {
    "case_id": "TC_LOGIN_010",
    "name": "����ɼ����л�����",
    "type": "functional",
    "description": "��֤����������Ҳ���۾�ͼ������л���������/������ʾ",
    "priority": "low",
    "steps": [
      {"action": "���������������Ѽ���", "expected": "������ʾΪԲ�����"},
      {"action": "������鿴�����Ҳ���۾�ͼ��", "expected": "��Ҳ�л�����Ϊ������ʾ"},
      {"action": "�ٴε���۾�ͼ��", "expected": "��ת�ָ���Ϊ������ʾ"}
    ],
    "expected_result": "����ɼ����л�����ʹ�������ѡ��ı仯��ʾ�û��й���",
    "tags": ["��¼", "�û�����", "����"]
  }
]
```', 'role': 'assistant', 'name': 'MiniMax AI', 'audio_content': '', 'reasoning_content': '...'''

print(f"Content length: {len(content)}")
print(f"Starts with: {repr(content[:20])}")
print(f"Ends with: {repr(content[-50:])}")

# 尝试解析
json_str = content.strip()

# 移除 fences
fences = ['```json', '```JSON', '```', '```json\n', '```\n']
for fence in fences:
    if json_str.startswith(fence):
        json_str = json_str[len(fence):].strip()
        print(f"Stripped '{fence}', now starts: {repr(json_str[:30])}")

print(f"After fence removal, starts: {repr(json_str[:20])}")
print(f"After fence removal, ends: {repr(json_str[-30:])}")

# 找JSON边界
json_start = json_str.find('[')
json_end = json_str.rfind(']') + 1

print(f"json_start={json_start}, json_end={json_end}")

if json_start >= 0 and json_end > json_start:
    extracted = json_str[json_start:json_end]
    print(f"Extracted length: {len(extracted)}")
    print(f"Extracted starts: {repr(extracted[:30])}")
    print(f"Extracted ends: {repr(extracted[-30:])}")

    if extracted.startswith('[') and extracted.endswith(']'):
        try:
            data = json.loads(extracted)
            print(f"SUCCESS: {len(data)} items")
        except json.JSONDecodeError as e:
            print(f"FAILED: {e}")
    else:
        print("Does not start with [ or end with ]")
else:
    print("Could not find JSON bounds")