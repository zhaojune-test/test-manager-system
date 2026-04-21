"""测试实际内容的解析"""
import json

# 实际内容 - 从debug输出中提取的关键部分
content = '''[{"case_id":"TC_LOGIN_001","name":"��ȷ�˺������¼�ɹ�","type":"functional","description":"ʹ����ȷ���û����������¼ϵͳ����֤�ܹ��ɹ�����ϵͳ������","priority":"high","steps":[{"action":"�ڵ�¼ҳ��������ȷ���û���","expected":"�û����������ʾ���������"},{"action":"�ڵ�¼ҳ��������ȷ������","expected":"������ʾΪ���ܷ���"},{"action":"�����¼��ť�驮س���","expected":"ҳ����ת��ϵͳ�����棬��ʾ�û���Ϣ"}],"expected_result":"��¼�ɹ���ϵͳ��ʾ�����棬������ʾ�û����ƻ�ͷ��","tags":["��¼","ð�̲���","P0"]},{"case_id":"TC_LOGIN_002","name":"���������¼ʧ��","type":"functional","description":"ʹ����ȷ���û����ʹ���������¼����֤ϵͳ�ľ��루������","priority":"high","steps":[{"action":"�ڵ�¼ҳ��������ȷ���û���","expected":"�û���������ʾ"},{"action":"�ڵ�¼ҳ��������������","expected":"������ʾΪ���ܷ���"},{"action":"�����¼��ť","expected":"ϵͳ�ľ��루������ʾ"}],"expected_result":"��¼ʧ�ù�ϵͳ���ʾ\\"�û�������ȷ\\"","tags":["��¼","��ȫ��","P0"]},{"case_id":"TC_LOGIN_010","name":"��¼�Ự��ʱ��֤","type":"functional","description":"��¼��ʱ�䲻������֤ϵͳ�Ự��ʱ��Ҫ����µ�¼","priority":"medium","steps":[{"action":"ʹ����ȷ���û����������¼ϵͳ","expected":"��¼�ɹ���ϵͳ�����棬��ʾ�û���Ϣ"},{"action":"��ϵͳ�н���һЩ�����ˣ�","expected":"ϵͳ�������У�ʾ��̴̱�ֻ"},{"action":"�ȴ������Ự��ʱʱ�䣨��30���ӣ�","expected":"ϵͳ��⵽��ʱ"},{"action":"�ڵ�ǰҳ�������Ӧ����","expected":"ϵͳ��ת����¼ҳ����ʾ��ʱ��ʾ"}],"expected_result":"��ʱ��δ������ϵͳ�Զ��ǳ�����ת����¼ҳ�棬��ʾ\\"�Ự�ѳ�ʱ�������µ�¼\\"��ʾ","tags":["��¼","�Ự����","��ȫ��","P1"]}]', 'role': 'assistant', 'name': 'MiniMax AI', 'audio_content': '', 'reasoning_content': '...'''

print(f"Content length: {len(content)}")
print(f"Last 100 chars: {repr(content[-100:])}")

# 尝试直接解析
try:
    data = json.loads(content)
    print(f"Direct parse SUCCESS: {len(data)} items")
except json.JSONDecodeError as e:
    print(f"Direct parse FAILED: {e}")

# 找到 JSON 数组边界
json_start = content.find('[')
json_end = content.rfind(']') + 1

print(f"json_start: {json_start}, json_end: {json_end}")

if json_start >= 0 and json_end > json_start:
    extracted = content[json_start:json_end]
    print(f"Extracted length: {len(extracted)}")
    print(f"Extracted ends: {repr(extracted[-50:])}")
    try:
        data = json.loads(extracted)
        print(f"Extracted parse SUCCESS: {len(data)} items")
    except json.JSONDecodeError as e:
        print(f"Extracted parse FAILED: {e}")