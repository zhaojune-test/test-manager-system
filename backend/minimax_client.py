"""
MiniMax 大模型集成模块
支持 MiniMax API 和 本地部署的模型
"""
import os
import json
import requests
from typing import Dict, List, Optional, Tuple


class MiniMaxClient:
    """MiniMax 大模型客户端"""

    # API 配置
    DEFAULT_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    LOCAL_API_URL = "http://localhost:8000/v1/chat/completions"

    def __init__(self, api_key: str = None, group_id: str = None, model: str = "minimax-m2.7", local: bool = False):
        """
        初始化 MiniMax 客户端

        Args:
            api_key: MiniMax API密钥
            group_id: MiniMax Group ID
            model: 模型名称，默认 minimax-m2.7
            local: 是否使用本地部署
        """
        self.api_key = api_key or os.getenv('MINIMAX_API_KEY', '')
        self.group_id = group_id or os.getenv('MINIMAX_GROUP_ID', '')
        self.model = model
        self.local = local

        if not local and not self.api_key:
            raise ValueError("需要设置 MINIMAX_API_KEY 环境变量或传入 api_key 参数")

        self.api_url = self.LOCAL_API_URL if local else self.DEFAULT_API_URL
        self.session = requests.Session()

    def _get_headers(self) -> Dict:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
        }

        if not self.local:
            headers["Authorization"] = f"Bearer {self.api_key}"
            if self.group_id:
                headers["GroupId"] = self.group_id

        return headers

    def chat(self, messages: List[Dict], **kwargs) -> Tuple[bool, Dict]:
        """
        发送对话请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数如 temperature, max_tokens 等

        Returns:
            (success, response_or_error)
        """
        headers = self._get_headers()

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
                timeout=300  # Increased to 5 minutes for complex prompts
            )
            response.raise_for_status()

            # 获取原始响应文本以便调试
            response_text = response.text
            print(f"[MiniMax API] Response status: {response.status_code}, length: {len(response_text)}")

            # 检查响应是否包含非JSON内容
            if response_text.strip().startswith('{'):
                result = json.loads(response_text)
            else:
                # 如果不是以 { 开头，可能包含调试信息或错误信息
                print(f"[MiniMax API] Non-JSON response: {response_text[:500]}")
                return False, f"API返回了非JSON格式响应: {response_text[:200]}"

            # 检查MiniMax特有的错误格式
            if 'error' in result:
                return False, result['error']

            # 检查base_resp错误格式（MiniMax API）
            if 'base_resp' in result:
                base_resp = result['base_resp']
                if isinstance(base_resp, dict) and base_resp.get('status_code', 0) != 0:
                    return False, base_resp.get('status_msg', 'API错误')

            return True, result

        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到MiniMax服务"
        except requests.exceptions.HTTPError as e:
            return False, f"API错误: {str(e)}"
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {str(e)}, 响应内容: {response_text[:200] if response_text else 'empty'}"
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
        system_prompt = """你是一名SAAS行业的高级测试工程师，擅长根据需求生成功能测试用例。

请直接返回JSON数组，不要任何额外内容。
每个测试用例包含：case_id, name, type="functional", description, priority, steps=[{action, expected}], expected_result, tags

只返回10个测试用例，用JSON数组表示。"""

        user_prompt = f"""项目背景：{project_context if project_context else 'SAAS企业管理系统'}

需求：{requirement_text}

请生成10个功能测试用例JSON数组。示例格式：
[{{"case_id":"TC_001","name":"测试名称","type":"functional","description":"描述","priority":"high","steps":[{{"action":"操作","expected":"预期"}}],"expected_result":"结果","tags":["标签"]}}]

只返回JSON数组，不要其他文字。"""

        success, result = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        if not success:
            return False, result

        # 解析返回的内容
        try:
            # MiniMax API 返回格式
            choices = result.get('choices')
            if choices and len(choices) > 0:
                content = choices[0].get('message', {}).get('content', '')
            elif 'messages' in result:
                # 某些版本返回格式
                messages = result.get('messages', [])
                if messages:
                    content = messages[-1].get('text', '')
                else:
                    content = ''
            else:
                return False, f"未知响应格式: {str(result)[:200]}"

            if not content:
                return False, "模型返回内容为空"

            # 尝试提取JSON数组
            # 直接找到第一个 [ 和最后一个 ] 来确定JSON边界
            first_bracket = content.find('[')
            last_bracket = content.rfind(']')

            if first_bracket >= 0 and last_bracket > first_bracket:
                # 提取 [ 到 ] 的内容
                extracted = content[first_bracket:last_bracket + 1]

                # 确保提取的内容以 [ 开头且以 ] 结尾
                if extracted.startswith('[') and extracted.endswith(']'):
                    try:
                        test_cases = json.loads(extracted)
                        return True, test_cases
                    except json.JSONDecodeError:
                        pass

                # 如果解析失败，尝试用正则提取每个case
                import re
                matches = re.findall(r'\{[^{}]*"case_id"[^{}]*\}', extracted)
                if matches:
                    valid_cases = []
                    for match in matches:
                        try:
                            case = json.loads(match)
                            if 'case_id' in case:
                                valid_cases.append(case)
                        except:
                            pass
                    if valid_cases:
                        return True, valid_cases

            return False, f"模型返回格式错误，无法解析测试用例"

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
            # MiniMax API 返回格式
            choices = result.get('choices')
            if choices and len(choices) > 0:
                content = choices[0].get('message', {}).get('content', '')
            elif 'messages' in result:
                messages = result.get('messages', [])
                if messages:
                    content = messages[-1].get('text', '')
                else:
                    content = ''
            else:
                return False, f"未知响应格式: {str(result)[:200]}"

            if not content:
                return False, "模型返回内容为空"

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


def get_minimax_client(api_key: str = None, group_id: str = None, model: str = "minimax-m2.7", local: bool = False) -> MiniMaxClient:
    """获取 MiniMax 客户端实例"""
    return MiniMaxClient(api_key=api_key, group_id=group_id, model=model, local=local)
