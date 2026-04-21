"""测试MiniMax API认证"""
import os
import sys
import json
import requests

# 用户需要提供真实的API Key
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
GROUP_ID = os.environ.get("MINIMAX_GROUP_ID", "")

print("=" * 50)
print("MiniMax API 认证测试")
print("=" * 50)

# 检查环境变量
print(f"\n1. 检查环境变量:")
print(f"   MINIMAX_API_KEY: {'已设置' if API_KEY else '未设置'}")
print(f"   MINIMAX_GROUP_ID: {'已设置' if GROUP_ID else '未设置'}")

# 如果没有环境变量，提示用户
if not API_KEY:
    print("\n请设置环境变量:")
    print("   Windows: set MINIMAX_API_KEY=你的API密钥")
    print("   或在代码中直接输入密钥进行测试")

# 测试不同的认证方式
test_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"

# 方法1: Bearer Token
print(f"\n2. 测试Bearer Token认证:")
headers_bearer = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
if GROUP_ID:
    headers_bearer["GroupId"] = GROUP_ID

payload = {
    "model": "MiniMax-Text-01",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

try:
    resp = requests.post(test_url, headers=headers_bearer, json=payload, timeout=30)
    print(f"   状态码: {resp.status_code}")
    result = resp.json()
    print(f"   响应: {json.dumps(result, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 50)