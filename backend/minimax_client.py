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
        system_prompt = """你是一名高级QA测试工程师，遵循BMad测试方法论。

## 核心原则
1. **测试目标**：验证功能正确性、用户体验、数据完整性和错误处理
2. **测试覆盖**：正向路径 + 边界值 + 异常场景 + 交互逻辑

## 测试用例设计规范

### 用例结构
每个测试用例必须包含：
- case_id: TC_XXX 格式（自增编号）
- name: 清晰的测试名称，包含"验证"二字
- type: "functional"
- description: 简短的测试目的描述
- priority: high(核心流程) / medium(一般功能) / low(辅助功能)
- tags: 标签数组，如["登录","正向","高优先级"]

### 测试步骤规范
steps 数组每项：
- action: 具体的操作描述（谁/做什么/在哪）
- expected: 明确的预期结果（应该看到什么/发生什么）

### 测试用例分类
1. **正向测试**：正常流程、必填项验证、数据合法性
2. **反向测试**：必填项缺失、格式错误、边界值、数据越界
3. **异常测试**：网络异常、超时、服务端错误处理
4. **交互测试**：多步骤流程、页面跳转、数据传递

## 输出要求

根据需求分析后，生成12-18个测试用例，覆盖上述所有分类。

返回格式：严格JSON数组，不要任何额外文字。
每个用例示例：
{"case_id":"TC_001","name":"验证正常登录成功","type":"functional","description":"使用正确的用户名密码登录系统","priority":"high","steps":[{"action":"输入正确的用户名","expected":"用户名显示在输入框"},{"action":"输入正确的密码","expected":"密码显示为***"},{"action":"点击登录按钮","expected":"跳转到首页，显示用户信息"}],"expected_result":"登录成功，进入系统主页","tags":["登录","正向","高优先级"],"module":"登录模块"}"""

        user_prompt = f"""## 项目背景
{project_context if project_context else 'SAAS企业管理系统'}

## 需求文档内容
{requirement_text}

请根据上述需求文档，生成完整的测试用例。
确保覆盖：正向流程、边界值、异常处理、交互逻辑。
生成12-18个测试用例。"""

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

    def generate_test_cases_from_images(self, images: List[Dict], module_name: str = "") -> Tuple[bool, List[Dict]]:
        """
        根据多张截图生成功能测试用例（视觉理解）

        Args:
            images: 图片数据列表，格式为 [{"filename": "xxx.png", "base64": "..."}, ...]
            module_name: 模块名称

        Returns:
            (success, test_cases_list_or_error)
        """
        system_prompt = """你是一名高级QA测试工程师，遵循BMad测试方法论。

## 核心原则
1. **测试目标**：验证功能正确性、用户体验、数据完整性和错误处理
2. **测试覆盖**：正向路径 + 边界值 + 异常场景 + 交互逻辑

## 测试用例设计规范

### 用例结构
每个测试用例必须包含：
- case_id: TC_XXX 格式（自增编号）
- name: 清晰的测试名称，包含"验证"二字
- type: "functional"
- description: 简短的测试目的描述
- priority: high(核心流程) / medium(一般功能) / low(辅助功能)
- tags: 标签数组，如["登录","正向","高优先级"]

### 测试步骤规范
steps 数组每项：
- action: 具体的操作描述（谁/做什么/在哪）
- expected: 明确的预期结果（应该看到什么/发生什么）

### 测试用例分类
1. **正向测试**：正常流程、必填项验证、数据合法性
2. **反向测试**：必填项缺失、格式错误、边界值、数据越界
3. **异常测试**：网络异常、超时、服务端错误处理
4. **交互测试**：多步骤流程、页面跳转、数据传递

## 输出要求

根据UI截图分析后，生成12-18个测试用例，覆盖上述所有分类。

返回格式：严格JSON数组，不要任何额外文字。
每个用例示例：
{"case_id":"TC_001","name":"验证正常登录成功","type":"functional","description":"使用正确的用户名密码登录系统","priority":"high","steps":[{"action":"输入正确的用户名","expected":"用户名显示在输入框"},{"action":"输入正确的密码","expected":"密码显示为***"},{"action":"点击登录按钮","expected":"跳转到首页，显示用户信息"}],"expected_result":"登录成功，进入系统主页","tags":["登录","正向","高优先级"],"module":"登录模块"}"""

        # 构建多模态消息内容
        content = [{"type": "text", "text": f"请分析这些UI截图，识别功能元素和交互流程。模块名称：{module_name if module_name else 'UI功能'}"}]
        for img in images:
            # 根据文件扩展名确定 MIME 类型
            filename = img.get("filename", "image.png")
            if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif filename.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif filename.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/png"
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img['base64']}"}
            })

        success, result = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=32000
        )

        if not success:
            print(f"[MiniMax Vision] API调用失败: {result}")
            return False, result

        print(f"[MiniMax Vision] 原始响应长度: {len(str(result))}")

        # 解析返回的内容
        try:
            # MiniMax API 返回格式
            print(f"[MiniMax Vision] result类型: {type(result)}, keys: {result.keys() if hasattr(result, 'keys') else 'N/A'}")
            choices = result.get('choices')
            print(f"[MiniMax Vision] choices: {choices}")
            if choices and len(choices) > 0:
                content_text = choices[0].get('message', {}).get('content', '')
                print(f"[MiniMax Vision] content_text类型: {type(content_text)}")
            elif 'messages' in result:
                messages = result.get('messages', [])
                if messages:
                    content_text = messages[-1].get('text', '')
                else:
                    content_text = ''
            else:
                print(f"[MiniMax Vision] 未知响应格式，result keys: {result.keys() if hasattr(result, 'keys') else 'not a dict'}")
                return False, f"未知响应格式: {str(result)[:200]}"

            if not content_text:
                return False, "模型返回内容为空"

            print(f"[MiniMax Vision] 解析到的content_text长度: {len(content_text)}")
            print(f"[MiniMax Vision] content_text前300字符: {content_text[:300]}")

            # 尝试提取JSON数组
            first_bracket = content_text.find('[')
            last_bracket = content_text.rfind(']')

            if first_bracket >= 0 and last_bracket > first_bracket:
                extracted = content_text[first_bracket:last_bracket + 1]
                if extracted.startswith('[') and extracted.endswith(']'):
                    try:
                        test_cases = json.loads(extracted)
                        return True, test_cases
                    except json.JSONDecodeError as e:
                        print(f"[MiniMax Vision] JSON解析失败: {e}")
                        pass

            # 如果完整JSON解析失败，尝试用正则提取每个完整的case对象
            import re
            # 匹配完整的JSON对象 { ... }
            pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(pattern, content_text)
            if matches:
                print(f"[MiniMax Vision] 正则匹配到 {len(matches)} 个对象")
                valid_cases = []
                for match in matches:
                    try:
                        case = json.loads(match)
                        if 'case_id' in case and 'name' in case:
                            valid_cases.append(case)
                    except:
                        pass
                if valid_cases:
                    print(f"[MiniMax Vision] 有效用例数: {len(valid_cases)}")
                    return True, valid_cases

            return False, f"模型返回格式错误，无法解析测试用例。返回内容: {content_text[:300]}"

        except (KeyError, json.JSONDecodeError) as e:
            return False, f"解析测试用例失败: {str(e)}"

    def generate_test_cases_from_images_and_text(self, images: List[Dict], text: str, module_name: str = "") -> Tuple[bool, List[Dict]]:
        """
        根据多张截图+文本需求生成功能测试用例（视觉理解+文本理解）

        Args:
            images: 图片数据列表，格式为 [{"filename": "xxx.png", "base64": "..."}, ...]
            text: 需求文档文本内容
            module_name: 模块名称

        Returns:
            (success, test_cases_list_or_error)
        """
        system_prompt = """你是一名高级QA测试工程师，遵循BMad测试方法论。

## 核心原则
1. **测试目标**：验证功能正确性、用户体验、数据完整性和错误处理
2. **测试覆盖**：正向路径 + 边界值 + 异常场景 + 交互逻辑
3. **输入理解**：同时分析UI截图和文字需求，二者结合理解完整功能

## 测试用例设计规范

### 用例结构
每个测试用例必须包含：
- case_id: TC_XXX 格式（自增编号）
- name: 清晰的测试名称，包含"验证"二字
- type: "functional"
- description: 简短的测试目的描述
- priority: high(核心流程) / medium(一般功能) / low(辅助功能)
- tags: 标签数组，如["登录","正向","高优先级"]

### 测试步骤规范
steps 数组每项：
- action: 具体的操作描述（谁/做什么/在哪）
- expected: 明确的预期结果（应该看到什么/发生什么）

### 测试用例分类
1. **正向测试**：正常流程、必填项验证、数据合法性
2. **反向测试**：必填项缺失、格式错误、边界值、数据越界
3. **异常测试**：网络异常、超时、服务端错误处理
4. **交互测试**：多步骤流程、页面跳转、数据传递

## 输出要求

根据UI截图和需求文档分析后，生成15-20个测试用例，覆盖上述所有分类。
截图展示的界面元素应与文字需求结合理解。

返回格式：严格JSON数组，不要任何额外文字。
每个用例示例：
{"case_id":"TC_001","name":"验证正常登录成功","type":"functional","description":"使用正确的用户名密码登录系统","priority":"high","steps":[{"action":"输入正确的用户名","expected":"用户名显示在输入框"},{"action":"输入正确的密码","expected":"密码显示为***"},{"action":"点击登录按钮","expected":"跳转到首页，显示用户信息"}],"expected_result":"登录成功，进入系统主页","tags":["登录","正向","高优先级"],"module":"登录模块"}"""

        # 构建多模态消息内容
        content = [{"type": "text", "text": f"【需求文档】\n{text}\n\n请分析这些UI截图，结合上述需求文档识别功能元素和交互流程。"}]
        for img in images:
            filename = img.get("filename", "image.png")
            if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif filename.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif filename.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/png"
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img['base64']}"}
            })

        success, result = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=32000
        )

        if not success:
            print(f"[MiniMax Vision+Text] API调用失败: {result}")
            return False, result

        print(f"[MiniMax Vision+Text] 原始响应长度: {len(str(result))}")

        # 解析返回的内容
        try:
            print(f"[MiniMax Vision+Text] result类型: {type(result)}, keys: {result.keys() if hasattr(result, 'keys') else 'N/A'}")
            choices = result.get('choices')
            print(f"[MiniMax Vision+Text] choices: {choices}")
            if choices and len(choices) > 0:
                content_text = choices[0].get('message', {}).get('content', '')
                print(f"[MiniMax Vision+Text] content_text类型: {type(content_text)}")
            elif 'messages' in result:
                messages = result.get('messages', [])
                if messages:
                    content_text = messages[-1].get('text', '')
                else:
                    content_text = ''
            else:
                return False, f"未知响应格式: {str(result)[:200]}"

            if not content_text:
                return False, "模型返回内容为空"

            print(f"[MiniMax Vision+Text] 解析到的content_text长度: {len(content_text)}")
            print(f"[MiniMax Vision+Text] content_text前300字符: {content_text[:300]}")

            first_bracket = content_text.find('[')
            last_bracket = content_text.rfind(']')

            if first_bracket >= 0 and last_bracket > first_bracket:
                extracted = content_text[first_bracket:last_bracket + 1]
                if extracted.startswith('[') and extracted.endswith(']'):
                    try:
                        test_cases = json.loads(extracted)
                        return True, test_cases
                    except json.JSONDecodeError as e:
                        print(f"[MiniMax Vision+Text] JSON解析失败: {e}")
                        pass

            # 如果完整JSON解析失败，尝试用正则提取每个完整的case对象
            import re
            pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(pattern, content_text)
            if matches:
                print(f"[MiniMax Vision+Text] 正则匹配到 {len(matches)} 个对象")
                valid_cases = []
                for match in matches:
                    try:
                        case = json.loads(match)
                        if 'case_id' in case and 'name' in case:
                            valid_cases.append(case)
                    except:
                        pass
                if valid_cases:
                    print(f"[MiniMax Vision+Text] 有效用例数: {len(valid_cases)}")
                    return True, valid_cases

            return False, f"模型返回格式错误，无法解析测试用例。返回内容: {content_text[:300]}"

        except (KeyError, json.JSONDecodeError) as e:
            return False, f"解析测试用例失败: {str(e)}"


def get_minimax_client(api_key: str = None, group_id: str = None, model: str = "minimax-m2.7", local: bool = False) -> MiniMaxClient:
    """获取 MiniMax 客户端实例"""
    return MiniMaxClient(api_key=api_key, group_id=group_id, model=model, local=local)
