"""测试MiniMax客户端"""
import os
import sys
sys.path.insert(0, '.')

from backend.minimax_client import MiniMaxClient

# 使用真实API Key测试
api_key = "sk-cp-cMEb6T2Rkx3xxx"  # 替换为你的真实API Key

print(f"Testing MiniMax client with API key: {api_key[:15]}...")
client = MiniMaxClient(api_key=api_key)

# 简单测试
messages = [
    {"role": "user", "content": "你好，返回JSON格式：[{\"test\": \"hello\"}]"}
]

print("Calling chat API...")
success, result = client.chat(messages)

print(f"\nSuccess: {success}")
print(f"Result type: {type(result)}")
if isinstance(result, dict):
    print(f"Result keys: {result.keys()}")
    print(f"Full result: {str(result)}")

if success:
    choices = result.get('choices')
    print(f"\nChoices: {choices}")
    if choices:
        content = choices[0].get('message', {}).get('content', '')
        print(f"Content: {content}")
else:
    print(f"Error: {result}")