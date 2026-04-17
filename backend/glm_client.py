"""
GLM-4 大模型集成模块
支持智谱AI GLM-4 API 和 本地部署的 GLM 模型
"""
import os
import json
import requests
from typing import Dict, List, Optional, Tuple


class GLMClient:
    """GLM-4 大模型客户端"""

    # API 配置
    DEFAULT_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    LOCAL_API_URL = "http://localhost:8000/v1/chat/completions"

    def __init__(self, api_key: str = None, model: str = "glm-4", local: bool = False):
        """
        初始化 GLM 客户端

        Args:
            api_key: 智谱AI API密钥（本地部署时可不填）
            model: 模型名称，默认 glm-4
            local: 是否使用本地部署
        """
        self.api_key = api_key or os.getenv('GLM_API_KEY', '')
        self.model = model
        self.local = local

        if not local and not self.api_key:
            raise ValueError("需要设置 GLM_API_KEY 环境变量或传入 api_key 参数")

        self.api_url = self.LOCAL_API_URL if local else self.DEFAULT_API_URL
        self.session = requests.Session()

    def chat(self, messages: List[Dict], **kwargs) -> Tuple[bool, Dict]:
        """
        发送对话请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数如 temperature, max_tokens 等

        Returns:
            (success, response_or_error)
        """
        headers = {
            "Content-Type": "application/json",
        }

        if not self.local:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }

        try:
            response = self.session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            result = response.json()

            if 'error' in result:
                return False, result['error']

            return True, result

        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到GLM服务"
        except requests.exceptions.HTTPError as e:
            return False, f"API错误: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def generate_test_cases(self, requirement_text: str, project_context: str = "") -> Tuple[bool, List[Dict]]:
        """
        根据需求生成测试用例

        Args:
            requirement_text: 需求文档内容
            project_context: 项目背景信息

        Returns:
            (success, test_cases_list_or_error)
        """
        system_prompt = """你是一个专业的测试工程师，擅长根据需求文档生成全面的功能测试用例。

请根据提供的产品需求文档，生成结构化的功能测试用例。

每个测试用例应包含：
- case_id: 用例编号（如 TC_001）
- name: 用例名称（简洁明确）
- type: 用例类型（填写 "functional"）
- description: 用例描述（简要说明测试目的）
- priority: 优先级（high/medium/low）
- steps: 测试步骤列表，每个步骤包含 action 和 expected
- expected_result: 预期结果

请以JSON数组格式返回测试用例列表。"""

        user_prompt = f"""## 项目背景
{project_context}

## 需求文档内容
{requirement_text}

请根据上述需求文档，生成完整的测试用例。
确保覆盖：
1. 功能正常流程
2. 边界条件和异常处理
3. 用户交互和界面响应
4. 数据验证和错误处理

请以JSON数组格式返回，示例：
[
  {{
    "case_id": "TC_001",
    "name": "验证用户登录成功",
    "type": "functional",
    "description": "验证使用正确的用户名和密码可以成功登录系统",
    "priority": "high",
    "steps": [
      {{"action": "输入用户名", "expected": "用户名显示在输入框"}},
      {{"action": "输入密码", "expected": "密码以*号显示"}},
      {{"action": "点击登录按钮", "expected": "跳转到首页"}}
    ],
    "expected_result": "登录成功，显示用户信息"
  }}
]"""

        success, result = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096
        )

        if not success:
            return False, result

        # 解析返回的内容
        try:
            content = result['choices'][0]['message']['content']

            # 尝试提取JSON数组
            json_match = None
            if '[' in content and ']' in content:
                start = content.find('[')
                end = content.rfind(']') + 1
                json_str = content[start:end]
                test_cases = json.loads(json_str)
                return True, test_cases

            return False, "模型返回格式错误，无法解析测试用例"

        except (KeyError, json.JSONDecodeError) as e:
            return False, f"解析测试用例失败: {str(e)}"

    def analyze_requirement(self, requirement_text: str) -> Tuple[bool, Dict]:
        """
        分析需求文档，提取关键信息

        Args:
            requirement_text: 需求文档内容

        Returns:
            (success, analysis_result)
        """
        system_prompt = """你是一个专业的需求分析师，擅长从文档中提取结构化的需求信息。

请分析提供的产品需求文档，提取以下信息并以JSON格式返回：
{
  "summary": "需求概要（100字以内）",
  "modules": ["模块1", "模块2", ...],
  "functional_points": ["功能点1", "功能点2", ...],
  "user_roles": ["用户角色1", "用户角色2", ...],
  "key_entities": ["关键实体1", "关键实体2", ...],
  "acceptance_criteria": ["验收标准1", "验收标准2", ...]
}"""

        success, result = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": requirement_text}
            ],
            temperature=0.3,
            max_tokens=2048
        )

        if not success:
            return False, result

        try:
            content = result['choices'][0]['message']['content']

            # 尝试提取JSON
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                analysis = json.loads(json_str)
                return True, analysis

            return False, "分析结果格式错误"

        except (KeyError, json.JSONDecodeError) as e:
            return False, f"解析分析结果失败: {str(e)}"


def get_glm_client(api_key: str = None, model: str = "glm-4", local: bool = False) -> GLMClient:
    """获取 GLM 客户端实例"""
    return GLMClient(api_key=api_key, model=model, local=local)
