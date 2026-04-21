"""测试超时问题"""
import sys
sys.path.insert(0, '.')

from backend.minimax_client import MiniMaxClient

API_KEY = "sk-cp-cMEbc1feKv9-tYj8kFLR_udkxVYSRpIf7g4Iv4Ja1crNgMSyNO2eJtybDKx0Dhyf2g_LpWBXoiqHTRjeIKgaA6O_VbWtERnctU3WfUn-3ES6uptaOhDvGhY"

print("Creating MiniMax client...")
client = MiniMaxClient(api_key=API_KEY)
print(f"Model: {client.model}")
print(f"API URL: {client.api_url}")
print(f"Timeout: 300 seconds")

print("\nTesting generate_test_cases (timeout now 300s)...")
success, result = client.generate_test_cases(
    requirement_text="用户登录功能测试",
    project_context="SAAS企业管理系统"
)

print(f"\nSuccess: {success}")
print(f"Result type: {type(result)}")
if isinstance(result, list):
    print(f"Number of test cases: {len(result)}")
    if result:
        print(f"First case: {result[0]}")
elif isinstance(result, str):
    print(f"Error message: {result}")
elif isinstance(result, dict):
    print(f"Result keys: {result.keys()}")