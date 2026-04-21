"""
测试用例自动生成模块
功能：基于AI或规则自动生成测试用例
"""
import os
import json
import uuid
import datetime


class TestGenerator:
    """测试用例生成器"""

    def __init__(self, test_cases_dir):
        self.test_cases_dir = test_cases_dir
        os.makedirs(test_cases_dir, exist_ok=True)

    def generate(self, description, test_type='api'):
        """
        生成测试用例

        Args:
            description: 功能描述
            test_type: 测试类型 (api 或 webui)

        Returns:
            生成的测试用例列表
        """
        if test_type == 'api':
            return self._generate_api_testcases(description)
        elif test_type == 'webui':
            return self._generate_webui_testcases(description)
        else:
            return []

    def _generate_api_testcases(self, description):
        """生成API测试用例"""
        # 基于描述生成常见的API测试场景
        testcases = []

        # 通用API测试场景
        common_scenarios = [
            {
                'name': '正常请求测试',
                'description': '验证API正常功能',
                'steps': [
                    {'action': '发送GET/POST请求', 'expected': '返回200状态码'},
                    {'action': '验证响应数据格式', 'expected': '返回正确的JSON格式'}
                ],
                'expected_result': '接口正常返回预期数据',
                'priority': 'high'
            },
            {
                'name': '参数为空测试',
                'description': '验证必填参数为空时的行为',
                'steps': [
                    {'action': '不传递必填参数', 'expected': '返回400或相应错误码'},
                    {'action': '验证错误信息', 'expected': '返回参数缺失的错误提示'}
                ],
                'expected_result': '返回适当的错误信息',
                'priority': 'high'
            },
            {
                'name': '参数边界测试',
                'description': '验证边界值处理',
                'steps': [
                    {'action': '传递空字符串', 'expected': '返回适当响应'},
                    {'action': '传递超长字符串', 'expected': '返回适当响应'}
                ],
                'expected_result': '正确处理边界值',
                'priority': 'medium'
            },
            {
                'name': '错误格式测试',
                'description': '验证错误数据格式处理',
                'steps': [
                    {'action': '发送格式错误的JSON', 'expected': '返回400错误'},
                    {'action': '验证错误信息', 'expected': '返回格式错误的提示'}
                ],
                'expected_result': '返回格式错误提示',
                'priority': 'medium'
            },
            {
                'name': '并发请求测试',
                'description': '验证并发请求处理',
                'steps': [
                    {'action': '同时发送多个请求', 'expected': '所有请求正常响应'},
                    {'action': '验证数据一致性', 'expected': '数据保持一致'}
                ],
                'expected_result': '并发请求正常处理',
                'priority': 'low'
            }
        ]

        for scenario in common_scenarios:
            testcases.append({
                'id': str(uuid.uuid4()),
                'name': f"{description} - {scenario['name']}",
                'type': 'api',
                'description': f"{description}: {scenario['description']}",
                'steps': scenario['steps'],
                'expected_result': scenario['expected_result'],
                'priority': scenario['priority'],
                'status': 'pending',
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'test_data': {
                    'url': 'http://localhost:8080/api/example',
                    'method': 'GET',
                    'headers': {'Content-Type': 'application/json'},
                    'params': {}
                }
            })

        return testcases

    def _generate_webui_testcases(self, description):
        """生成Web UI测试用例"""
        testcases = []

        common_scenarios = [
            {
                'name': '页面加载测试',
                'description': '验证页面正常加载',
                'steps': [
                    {'action': '打开目标页面', 'expected': '页面成功加载'},
                    {'action': '检查页面标题', 'expected': '标题正确显示'}
                ],
                'expected_result': '页面正常加载，无错误',
                'priority': 'high'
            },
            {
                'name': '元素存在性测试',
                'description': '验证关键元素存在',
                'steps': [
                    {'action': '定位关键元素', 'expected': '元素可见'},
                    {'action': '验证元素文本', 'expected': '文本内容正确'}
                ],
                'expected_result': '关键元素正确显示',
                'priority': 'high'
            },
            {
                'name': '表单输入测试',
                'description': '验证表单输入功能',
                'steps': [
                    {'action': '在输入框中输入内容', 'expected': '内容正确输入'},
                    {'action': '清空输入内容', 'expected': '内容被清空'}
                ],
                'expected_result': '表单输入功能正常',
                'priority': 'high'
            },
            {
                'name': '按钮点击测试',
                'description': '验证按钮点击功能',
                'steps': [
                    {'action': '点击按钮', 'expected': '按钮响应点击事件'},
                    {'action': '验证按钮状态变化', 'expected': '状态正确变化'}
                ],
                'expected_result': '按钮点击功能正常',
                'priority': 'high'
            },
            {
                'name': '错误提示测试',
                'description': '验证错误信息显示',
                'steps': [
                    {'action': '触发错误场景', 'expected': '显示错误提示'},
                    {'action': '验证错误信息内容', 'expected': '错误信息准确'}
                ],
                'expected_result': '错误提示正确显示',
                'priority': 'medium'
            },
            {
                'name': '响应式布局测试',
                'description': '验证不同屏幕尺寸下的显示',
                'steps': [
                    {'action': '调整浏览器窗口大小', 'expected': '布局自适应'},
                    {'action': '验证关键元素可见性', 'expected': '元素正确显示'}
                ],
                'expected_result': '响应式布局正常',
                'priority': 'low'
            }
        ]

        for scenario in common_scenarios:
            testcases.append({
                'id': str(uuid.uuid4()),
                'name': f"{description} - {scenario['name']}",
                'type': 'webui',
                'description': f"{description}: {scenario['description']}",
                'steps': scenario['steps'],
                'expected_result': scenario['expected_result'],
                'priority': scenario['priority'],
                'status': 'pending',
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'test_data': {
                    'url': 'http://localhost:3000',
                    'selectors': {
                        'main': 'body',
                        'button': 'button.primary',
                        'input': 'input[type="text"]'
                    }
                }
            })

        return testcases

    def generate_from_api_spec(self, api_spec):
        """
        根据API规范生成测试用例

        Args:
            api_spec: API规范 (OpenAPI格式)

        Returns:
            生成的测试用例列表
        """
        testcases = []

        if 'paths' in api_spec:
            for path, methods in api_spec['paths'].items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        testcase = {
                            'id': str(uuid.uuid4()),
                            'name': f"{method.upper()} {path}",
                            'type': 'api',
                            'description': details.get('summary', ''),
                            'steps': [
                                {'action': f'发送{method.upper()}请求到{path}', 'expected': '返回预期响应'}
                            ],
                            'expected_result': '接口返回正确结果',
                            'priority': 'high',
                            'status': 'pending',
                            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'test_data': {
                                'url': f'http://localhost:8080{path}',
                                'method': method.upper(),
                                'headers': {'Content-Type': 'application/json'},
                                'params': details.get('parameters', [])
                            }
                        }
                        testcases.append(testcase)

        return testcases
