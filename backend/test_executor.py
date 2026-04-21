"""
测试执行模块
功能：执行API测试和Web UI测试
"""
import os
import json
import uuid
import datetime
import time
import requests
from typing import List, Dict


class TestExecutor:
    """测试执行器"""

    def __init__(self, test_cases_dir):
        self.test_cases_dir = test_cases_dir
        self.data_dir = os.path.join(os.path.dirname(test_cases_dir), 'data')
        os.makedirs(self.data_dir, exist_ok=True)

    def load_testcases(self):
        """加载测试用例"""
        testcases_file = os.path.join(self.data_dir, 'testcases.json')
        if os.path.exists(testcases_file):
            with open(testcases_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def run(self, case_ids: List[str]) -> List[Dict]:
        """执行指定的测试用例"""
        testcases = self.load_testcases()
        results = []

        for case_id in case_ids:
            for case in testcases:
                if case['id'] == case_id:
                    result = self._execute_testcase(case)
                    results.append(result)
                    break

        return results

    def run_all(self) -> List[Dict]:
        """执行所有测试用例"""
        testcases = self.load_testcases()
        results = []

        for case in testcases:
            result = self._execute_testcase(case)
            results.append(result)

        return results

    def _execute_testcase(self, testcase: Dict) -> Dict:
        """执行单个测试用例"""
        result = {
            'id': str(uuid.uuid4()),
            'case_id': testcase['id'],
            'case_name': testcase['name'],
            'case_type': testcase.get('type', 'api'),
            'status': 'pending',
            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': None,
            'duration': 0,
            'steps_result': [],
            'error': None
        }

        start_time = time.time()

        try:
            if testcase.get('type', 'api') == 'api':
                self._execute_api_test(testcase, result)
            elif testcase.get('type') == 'webui':
                self._execute_webui_test(testcase, result)
            else:
                result['status'] = 'skipped'
                result['error'] = '未知的测试类型'
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        end_time = time.time()
        result['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['duration'] = round(end_time - start_time, 2)

        return result

    def _execute_api_test(self, testcase: Dict, result: Dict):
        """执行API测试"""
        test_data = testcase.get('test_data', {})

        url = test_data.get('url', '')
        method = test_data.get('method', 'GET').upper()
        headers = test_data.get('headers', {})
        params = test_data.get('params', {})
        body = test_data.get('body', {})

        if not url:
            result['status'] = 'skipped'
            result['error'] = '未配置测试URL'
            return

        # 执行HTTP请求
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=body, params=params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=body, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=body, params=params, timeout=30)
            else:
                result['status'] = 'skipped'
                result['error'] = f'不支持的HTTP方法: {method}'
                return

            # 记录步骤结果
            step_result = {
                'step': f'发送{method}请求到{url}',
                'status': 'passed',
                'actual': f'状态码: {response.status_code}'
            }
            result['steps_result'].append(step_result)

            # 验证响应
            if 200 <= response.status_code < 300:
                result['status'] = 'passed'
            else:
                result['status'] = 'failed'
                result['error'] = f'HTTP错误: {response.status_code}'

        except requests.exceptions.ConnectionError:
            result['status'] = 'failed'
            result['error'] = '连接失败，请检查服务是否启动'
        except requests.exceptions.Timeout:
            result['status'] = 'failed'
            result['error'] = '请求超时'
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

    def _execute_webui_test(self, testcase: Dict, result: Dict):
        """执行Web UI测试"""
        # 注意：完整的Web UI测试需要安装playwright
        # 这里提供一个基础实现

        test_data = testcase.get('test_data', {})
        url = test_data.get('url', '')

        if not url:
            result['status'] = 'skipped'
            result['error'] = '未配置测试URL'
            return

        # 尝试导入playwright
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    # 访问页面
                    page.goto(url, wait_until='networkidle', timeout=30000)

                    step_result = {
                        'step': f'打开页面: {url}',
                        'status': 'passed',
                        'actual': '页面加载成功'
                    }
                    result['steps_result'].append(step_result)

                    # 检查页面标题
                    title = page.title()
                    step_result = {
                        'step': '获取页面标题',
                        'status': 'passed',
                        'actual': f'标题: {title}'
                    }
                    result['steps_result'].append(step_result)

                    result['status'] = 'passed'

                except Exception as e:
                    result['status'] = 'failed'
                    result['error'] = str(e)
                finally:
                    browser.close()

        except ImportError:
            # 如果没有安装playwright，尝试使用selenium
            try:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service

                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')

                driver = webdriver.Chrome(options=options)

                try:
                    driver.get(url)
                    time.sleep(2)

                    step_result = {
                        'step': f'打开页面: {url}',
                        'status': 'passed',
                        'actual': '页面加载成功'
                    }
                    result['steps_result'].append(step_result)

                    result['status'] = 'passed'

                except Exception as e:
                    result['status'] = 'failed'
                    result['error'] = str(e)
                finally:
                    driver.quit()

            except ImportError:
                result['status'] = 'skipped'
                result['error'] = '请安装playwright或selenium以执行Web UI测试'

    def run_batch(self, case_ids: List[str], concurrency: int = 1) -> List[Dict]:
        """
        批量执行测试用例

        Args:
            case_ids: 测试用例ID列表
            concurrency: 并发数

        Returns:
            测试结果列表
        """
        if concurrency <= 1:
            return self.run(case_ids)

        # TODO: 实现并发执行
        return self.run(case_ids)
