"""直接测试MiniMax API"""
import sys
sys.path.insert(0, '.')

from backend.minimax_client import MiniMaxClient

# 使用你的API Key测试
api_key = input("请输入MiniMax API Key: ").strip()
group_id = input("请输入Group ID (可选): ").strip()

client = MiniMaxClient(api_key=api_key, group_id=group_id if group_id else None)

# 简单的测试prompt
messages = [
    {"role": "user", "content": "请用JSON数组格式返回2个测试用例，格式如：[{\"case_id\": \"TC_001\", \"name\": \"测试名称\", \"type\": \"functional\", \"description\": \"描述\", \"priority\": \"high\", \"steps\": [{\"action\": \"操作\", \"expected\": \"预期\"}], \"expected_result\": \"结果\"}]。主题：用户登录功能"}
]

print("正在调用MiniMax API...")
success, result = client.chat(messages)

print(f"\n成功: {success}")
print(f"结果类型: {type(result)}")
if isinstance(result, dict):
    print(f"结果keys: {result.keys()}")
    print(f"结果: {str(result)[:1000]}")

if success:
    choices = result.get('choices')
    print(f"\nchoices: {choices}")
    if choices and len(choices) > 0:
        content = choices[0].get('message', {}).get('content', '')
        print(f"\ncontent: {content}")
else:
    print(f"错误: {result}")