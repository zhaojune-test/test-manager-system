"""
测试管理系统 - 后端API服务
功能：测试用例管理、自动生成、执行测试、生成报告
"""
import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.test_generator import TestGenerator
from backend.test_executor import TestExecutor
from backend.report_generator import ReportGenerator

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'))
CORS(app)

# 配置
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
TEST_CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cases')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEST_CASES_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# 初始化模块
test_generator = TestGenerator(TEST_CASES_DIR)
test_executor = TestExecutor(TEST_CASES_DIR)
report_generator = ReportGenerator(REPORTS_DIR)


def load_json(filepath):
    """加载JSON文件"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_json(filepath, data):
    """保存JSON文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 测试用例管理 API ====================

@app.route('/api/testcases', methods=['GET'])
def get_testcases():
    """获取测试用例（支持分页）"""
    testcases = load_json(os.path.join(DATA_DIR, 'testcases.json'))

    # 分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str).lower()
    method_filter = request.args.get('method', '', type=str)

    # 过滤
    if search or method_filter:
        filtered = []
        for c in testcases:
            match = True
            if search and search not in c.get('name', '').lower() and search not in c.get('description', '').lower():
                match = False
            if method_filter and c.get('test_data', {}).get('method', '') != method_filter:
                match = False
            if match:
                filtered.append(c)
        testcases = filtered

    total = len(testcases)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = testcases[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/testcases', methods=['POST'])
def create_testcase():
    """创建测试用例（兼容旧版本）"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'testcases.json'))

    new_case = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', ''),
        'type': data.get('type', 'api'),
        'description': data.get('description', ''),
        'steps': data.get('steps', []),
        'expected_result': data.get('expected_result', ''),
        'priority': data.get('priority', 'medium'),
        'status': 'pending',
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    testcases.append(new_case)
    save_json(os.path.join(DATA_DIR, 'testcases.json'), testcases)

    return jsonify({'success': True, 'data': new_case})


@app.route('/api/testcases/<case_id>', methods=['PUT'])
def update_testcase(case_id):
    """更新测试用例（兼容旧版本）"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'testcases.json'))

    for i, case in enumerate(testcases):
        if case['id'] == case_id:
            testcases[i].update(data)
            testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_json(os.path.join(DATA_DIR, 'testcases.json'), testcases)
            return jsonify({'success': True, 'data': testcases[i]})

    return jsonify({'success': False, 'message': '测试用例不存在'}), 404


@app.route('/api/testcases/<case_id>', methods=['DELETE'])
def delete_testcase(case_id):
    """删除测试用例（兼容旧版本）"""
    testcases = load_json(os.path.join(DATA_DIR, 'testcases.json'))
    testcases = [c for c in testcases if c['id'] != case_id]
    save_json(os.path.join(DATA_DIR, 'testcases.json'), testcases)
    return jsonify({'success': True})


# ==================== 功能测试用例 API ====================

@app.route('/api/functional/testcases', methods=['GET'])
def get_functional_testcases():
    """获取功能测试用例（支持分页）"""
    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str).lower()
    requirement = request.args.get('requirement', '', type=str).lower()

    if search or requirement:
        filtered = []
        for c in testcases:
            match = True
            if search and search not in c.get('name', '').lower() and search not in c.get('description', '').lower():
                match = False
            if requirement and requirement not in c.get('requirement_title', '').lower():
                match = False
            if match:
                filtered.append(c)
        testcases = filtered

    total = len(testcases)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = testcases[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/functional/testcases', methods=['POST'])
def create_functional_testcase():
    """创建功能测试用例"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))

    new_case = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', ''),
        'type': 'functional',
        'module': data.get('module', ''),
        'description': data.get('description', ''),
        'steps': data.get('steps', []),
        'expected_result': data.get('expected_result', ''),
        'priority': data.get('priority', 'medium'),
        'status': 'pending',
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    testcases.append(new_case)
    save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

    return jsonify({'success': True, 'data': new_case})


@app.route('/api/functional/testcases/<case_id>', methods=['PUT'])
def update_functional_testcase(case_id):
    """更新功能测试用例"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))

    for i, case in enumerate(testcases):
        if case['id'] == case_id:
            testcases[i].update(data)
            testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)
            return jsonify({'success': True, 'data': testcases[i]})

    return jsonify({'success': False, 'message': '测试用例不存在'}), 404


@app.route('/api/functional/testcases/<case_id>', methods=['DELETE'])
def delete_functional_testcase(case_id):
    """删除功能测试用例"""
    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
    testcases = [c for c in testcases if c['id'] != case_id]
    save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)
    return jsonify({'success': True})


@app.route('/api/functional/testcases/batch-delete', methods=['POST'])
def batch_delete_functional_testcases():
    """批量删除功能测试用例"""
    data = request.json
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'success': False, 'message': '请选择要删除的测试用例'}), 400

    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
    original_count = len(testcases)
    testcases = [c for c in testcases if c['id'] not in ids]
    deleted_count = original_count - len(testcases)

    save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)
    return jsonify({'success': True, 'data': {'deleted_count': deleted_count}})


@app.route('/api/functional/testcases/run', methods=['POST'])
def run_functional_tests():
    """执行功能测试用例（单个或批量）"""
    data = request.json
    case_ids = data.get('case_ids', [])
    status = data.get('status', 'passed')  # passed 或 failed
    error_msg = data.get('error', '')

    if not case_ids:
        return jsonify({'success': False, 'message': '请选择要执行的测试用例'}), 400

    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
    results = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for case in testcases:
        if case['id'] in case_ids:
            # 更新用例状态
            case['status'] = status
            case['updated_at'] = now

            # 创建执行记录
            result = {
                'id': str(uuid.uuid4()),
                'case_id': case['id'],
                'case_name': case['name'],
                'case_type': 'functional',
                'status': status,
                'start_time': now,
                'end_time': now,
                'duration': 0,
                'steps_result': case.get('steps', []),
                'error': error_msg if status == 'failed' else None
            }
            results.append(result)

    # 保存更新后的用例状态
    save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

    # 保存执行结果
    results_file = os.path.join(DATA_DIR, 'test_results.json')
    all_results = load_json(results_file)
    all_results.extend(results)
    save_json(results_file, all_results)

    return jsonify({'success': True, 'data': results})


# ==================== 需求管理 API ====================

@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    """获取需求列表（支持分页）"""
    requirements = load_json(os.path.join(DATA_DIR, 'requirements.json'))

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str).lower()

    if search:
        filtered = [r for r in requirements if search in r.get('title', '').lower() or search in r.get('description', '').lower()]
        requirements = filtered

    total = len(requirements)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = requirements[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/requirements', methods=['POST'])
def create_requirement():
    """创建需求"""
    data = request.json
    requirements = load_json(os.path.join(DATA_DIR, 'requirements.json'))

    new_req = {
        'id': str(uuid.uuid4()),
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    requirements.append(new_req)
    save_json(os.path.join(DATA_DIR, 'requirements.json'), requirements)

    return jsonify({'success': True, 'data': new_req})


@app.route('/api/requirements/<req_id>', methods=['PUT'])
def update_requirement(req_id):
    """更新需求"""
    data = request.json
    requirements = load_json(os.path.join(DATA_DIR, 'requirements.json'))

    for i, req in enumerate(requirements):
        if req['id'] == req_id:
            requirements[i].update(data)
            requirements[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_json(os.path.join(DATA_DIR, 'requirements.json'), requirements)
            return jsonify({'success': True, 'data': requirements[i]})

    return jsonify({'success': False, 'message': '需求不存在'}), 404


@app.route('/api/requirements/<req_id>', methods=['DELETE'])
def delete_requirement(req_id):
    """删除需求"""
    requirements = load_json(os.path.join(DATA_DIR, 'requirements.json'))
    requirements = [r for r in requirements if r['id'] != req_id]
    save_json(os.path.join(DATA_DIR, 'requirements.json'), requirements)
    return jsonify({'success': True})


@app.route('/api/functional/testcases/batch-update-requirement', methods=['POST'])
def batch_update_testcase_requirement():
    """批量更新测试用例的需求关联"""
    data = request.json
    ids = data.get('ids', [])
    requirement_title = data.get('requirement_title', '')

    if not ids:
        return jsonify({'success': False, 'message': '请选择要关联的测试用例'}), 400

    testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
    updated_count = 0

    for i, case in enumerate(testcases):
        if case['id'] in ids:
            testcases[i]['requirement_title'] = requirement_title
            testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_count += 1

    save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)
    return jsonify({'success': True, 'data': {'updated_count': updated_count}})


# ==================== 接口测试用例 API ====================

@app.route('/api/api/testcases', methods=['GET'])
def get_api_testcases():
    """获取接口测试用例（支持分页）"""
    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))

    # 分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str).lower()
    method_filter = request.args.get('method', '', type=str)

    # 过滤
    if search or method_filter:
        filtered = []
        for c in testcases:
            match = True
            if search and search not in c.get('name', '').lower() and search not in c.get('description', '').lower():
                match = False
            if method_filter and c.get('test_data', {}).get('method', '') != method_filter:
                match = False
            if match:
                filtered.append(c)
        testcases = filtered

    total = len(testcases)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = testcases[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/api/testcases', methods=['POST'])
def create_api_testcase():
    """创建接口测试用例"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))

    new_case = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', ''),
        'type': 'api',
        'description': data.get('description', ''),
        'steps': data.get('steps', []),
        'expected_result': data.get('expected_result', ''),
        'priority': data.get('priority', 'medium'),
        'status': 'pending',
        'test_data': data.get('test_data', {}),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    testcases.append(new_case)
    save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)

    return jsonify({'success': True, 'data': new_case})


@app.route('/api/api/testcases/<case_id>', methods=['PUT'])
def update_api_testcase(case_id):
    """更新接口测试用例"""
    data = request.json
    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))

    for i, case in enumerate(testcases):
        if case['id'] == case_id:
            testcases[i].update(data)
            testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)
            return jsonify({'success': True, 'data': testcases[i]})

    return jsonify({'success': False, 'message': '测试用例不存在'}), 404


@app.route('/api/api/testcases/<case_id>', methods=['DELETE'])
def delete_api_testcase(case_id):
    """删除接口测试用例"""
    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))
    testcases = [c for c in testcases if c['id'] != case_id]
    save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)
    return jsonify({'success': True})


@app.route('/api/api/testcases/batch-delete', methods=['POST'])
def batch_delete_api_testcases():
    """批量删除接口测试用例"""
    data = request.json
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'success': False, 'message': '请选择要删除的测试用例'}), 400

    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))
    original_count = len(testcases)
    testcases = [c for c in testcases if c['id'] not in ids]
    deleted_count = original_count - len(testcases)

    save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)
    return jsonify({'success': True, 'data': {'deleted_count': deleted_count}})


@app.route('/api/api/tests/run', methods=['POST'])
def run_api_tests():
    """执行指定的接口测试用例"""
    data = request.json or {}
    case_ids = data.get('case_ids', [])

    if not case_ids:
        return jsonify({'success': False, 'message': '请选择要执行的测试用例'}), 400

    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))
    results = []

    for case_id in case_ids:
        for i, case in enumerate(testcases):
            if case['id'] == case_id:
                result = execute_api_test(case)
                results.append(result)
                # 更新用例状态
                testcases[i]['status'] = result['status']
                testcases[i]['last_result'] = result
                testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

    # 保存更新后的状态
    save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)

    # 保存执行记录
    save_execution_results(results)

    return jsonify({'success': True, 'data': results})


@app.route('/api/api/tests/run-all', methods=['POST'])
def run_all_api_tests():
    """执行所有接口测试用例"""
    testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))
    results = []

    for i, case in enumerate(testcases):
        result = execute_api_test(case)
        results.append(result)
        # 更新用例状态
        testcases[i]['status'] = result['status']
        testcases[i]['last_result'] = result
        testcases[i]['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 保存更新后的状态
    save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)

    # 保存执行记录
    save_execution_results(results)

    return jsonify({'success': True, 'data': results})


def save_execution_results(results):
    """保存执行结果到历史记录"""
    if not results:
        return

    history_file = os.path.join(DATA_DIR, 'api_test_results.json')
    history = []

    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    # 添加新结果
    history.extend(results)

    # 只保留最近100条记录
    if len(history) > 100:
        history = history[-100:]

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def execute_api_test(testcase: dict) -> dict:
    """执行单个接口测试用例"""
    import time
    import requests
    from datetime import datetime

    result = {
        'id': str(uuid.uuid4()),
        'case_id': testcase['id'],
        'case_name': testcase['name'],
        'method': testcase.get('method', 'GET'),
        'url': testcase.get('test_data', {}).get('url', ''),
        'status': 'pending',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': None,
        'duration': 0,
        'response_status': 0,
        'response_body': None,
        'error': None
    }

    start_time = time.time()

    try:
        test_data = testcase.get('test_data', {})
        url = test_data.get('url', '')
        method = test_data.get('method', 'GET').upper()
        headers = test_data.get('headers', {})
        params = test_data.get('params', {})
        body = test_data.get('body', {})

        if not url:
            result['status'] = 'skipped'
            result['error'] = '未配置测试URL'
            return result

        # 执行HTTP请求
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
            return result

        result['response_status'] = response.status_code
        try:
            result['response_body'] = response.json() if response.content else None
        except:
            result['response_body'] = response.text[:500] if response.content else None

        # 验证响应
        if 200 <= response.status_code < 300:
            result['status'] = 'passed'
        elif response.status_code >= 400:
            result['status'] = 'failed'
            result['error'] = f'HTTP错误: {response.status_code}'
        else:
            result['status'] = 'passed'

    except requests.exceptions.ConnectionError as e:
        result['status'] = 'failed'
        result['error'] = f'连接失败: {str(e)}'
    except requests.exceptions.Timeout:
        result['status'] = 'failed'
        result['error'] = '请求超时（30秒）'
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)

    end_time = time.time()
    result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result['duration'] = round(end_time - start_time, 3)

    return result


# ==================== 执行记录 API ====================

@app.route('/api/api/results', methods=['GET'])
def get_api_results():
    """获取接口测试执行记录（支持分页）"""
    history_file = os.path.join(DATA_DIR, 'api_test_results.json')

    if not os.path.exists(history_file):
        return jsonify({'success': True, 'data': [], 'pagination': {'page': 1, 'page_size': 10, 'total': 0, 'total_pages': 0}})

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # 按执行时间倒序排列
        history.sort(key=lambda x: x.get('start_time', ''), reverse=True)

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        total = len(history)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = history[start:end]

        return jsonify({
            'success': True,
            'data': paginated,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/api/results/clear', methods=['POST'])
def clear_api_results():
    """清空执行记录"""
    history_file = os.path.join(DATA_DIR, 'api_test_results.json')

    try:
        if os.path.exists(history_file):
            os.remove(history_file)
        return jsonify({'success': True, 'message': '执行记录已清空'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/api/results/report', methods=['GET'])
def get_api_results_report():
    """获取执行记录统计报告"""
    history_file = os.path.join(DATA_DIR, 'api_test_results.json')

    if not os.path.exists(history_file):
        return jsonify({'success': True, 'data': {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'pass_rate': '0%',
            'total_duration': 0,
            'avg_duration': 0
        }})

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        total = len(history)
        passed = len([r for r in history if r.get('status') == 'passed'])
        failed = len([r for r in history if r.get('status') == 'failed'])
        skipped = len([r for r in history if r.get('status') == 'skipped'])

        durations = [r.get('duration', 0) for r in history if r.get('duration')]
        total_duration = sum(durations)
        avg_duration = total_duration / len(durations) if durations else 0

        pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"

        return jsonify({'success': True, 'data': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': pass_rate,
            'total_duration': round(total_duration, 3),
            'avg_duration': round(avg_duration, 3)
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== HAR 导入 API ====================

@app.route('/api/api/import-har', methods=['POST'])
def import_har_file():
    """导入 HAR 文件并生成接口测试用例"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择 HAR 文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    # 检查文件格式
    if not file.filename.lower().endswith('.har'):
        return jsonify({'success': False, 'message': '请上传 .har 格式的文件'}), 400

    try:
        # 保存上传的 HAR 文件
        upload_dir = os.path.join(DATA_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 解析 HAR 文件
        from backend.har_parser import parse_har_file

        success, result = parse_har_file(file_path)

        if not success:
            return jsonify({'success': False, 'message': result}), 400

        endpoints = result.get('endpoints', [])
        summary = result.get('summary', {})

        if not endpoints:
            return jsonify({'success': False, 'message': '未能从 HAR 文件中提取到有效的 API 请求'}), 400

        # 保存到接口测试用例
        testcases = load_json(os.path.join(DATA_DIR, 'api_testcases.json'))
        existing_ids = {case['id'] for case in testcases}

        added_count = 0
        for endpoint in endpoints:
            # 保持原有 ID 或生成新的
            case_id = endpoint.get('id', str(uuid.uuid4()))
            if case_id in existing_ids:
                case_id = str(uuid.uuid4())

            new_case = {
                'id': case_id,
                'name': endpoint.get('name', f"API_{endpoint.get('method', 'GET')}"),
                'type': 'api',
                'description': endpoint.get('description', ''),
                'method': endpoint.get('method', 'GET'),
                'url': endpoint.get('url', ''),
                'domain': endpoint.get('domain', ''),
                'path': endpoint.get('path', ''),
                'priority': endpoint.get('priority', 'medium'),
                'status': 'pending',
                'test_data': endpoint.get('test_data', {}),
                'response_status': endpoint.get('response_status', 0),
                'headers': endpoint.get('headers', {}),
                'params': endpoint.get('params', {}),
                'body': endpoint.get('body'),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            testcases.append(new_case)
            existing_ids.add(case_id)
            added_count += 1

        save_json(os.path.join(DATA_DIR, 'api_testcases.json'), testcases)

        return jsonify({
            'success': True,
            'data': {
                'count': added_count,
                'summary': summary,
                'message': f'成功导入 {added_count} 个接口测试用例'
            }
        })

    except Exception as e:
        import traceback
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}\n{traceback.format_exc()}'}), 500


@app.route('/api/api/parse-har', methods=['POST'])
def parse_har_preview():
    """预览 HAR 文件内容（不保存）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择 HAR 文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    # 检查文件格式
    if not file.filename.lower().endswith('.har'):
        return jsonify({'success': False, 'message': '请上传 .har 格式的文件'}), 400

    try:
        # 保存上传的 HAR 文件到临时位置
        upload_dir = os.path.join(DATA_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 解析 HAR 文件
        from backend.har_parser import parse_har_file

        success, result = parse_har_file(file_path)

        # 删除临时文件
        try:
            os.remove(file_path)
        except:
            pass

        if not success:
            return jsonify({'success': False, 'message': result}), 400

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'解析失败: {str(e)}'}), 500


# ==================== 导入功能 API ====================

@app.route('/api/functional/import', methods=['POST'])
def import_functional_testcases():
    """导入功能测试用例（Excel/CSV）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    try:
        # 尝试导入Excel
        try:
            import pandas as pd
            from io import BytesIO

            # 读取文件
            df = pd.read_excel(file) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(file)

            # 转换为测试用例
            testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))

            # 获取所有可能的列名映射
            for _, row in df.iterrows():
                # 尝试多种可能的列名
                name = (str(row.get('用例名称')) if pd.notna(row.get('用例名称')) else None) or \
                       (str(row.get('name')) if pd.notna(row.get('name')) else None) or \
                       (str(row.get('case_name')) if pd.notna(row.get('case_name')) else None) or \
                       (str(row.get('CaseName')) if pd.notna(row.get('CaseName')) else None) or \
                       (str(row.get('测试用例')) if pd.notna(row.get('测试用例')) else None) or \
                       (str(row.get('用例')) if pd.notna(row.get('用例')) else None) or '未命名'

                module = (str(row.get('功能模块')) if pd.notna(row.get('功能模块')) else None) or \
                         (str(row.get('module')) if pd.notna(row.get('module')) else None) or \
                         (str(row.get('模块')) if pd.notna(row.get('模块')) else None) or ''

                description = (str(row.get('描述')) if pd.notna(row.get('描述')) else None) or \
                              (str(row.get('description')) if pd.notna(row.get('description')) else None) or ''

                expected_result = (str(row.get('预期结果')) if pd.notna(row.get('预期结果')) else None) or \
                                  (str(row.get('expected_result')) if pd.notna(row.get('expected_result')) else None) or \
                                  (str(row.get('期望结果')) if pd.notna(row.get('期望结果')) else None) or ''

                priority = (str(row.get('优先级')) if pd.notna(row.get('优先级')) else None) or \
                           (str(row.get('priority')) if pd.notna(row.get('priority')) else None) or 'medium'

                new_case = {
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'type': 'functional',
                    'module': module,
                    'description': description,
                    'steps': [],
                    'expected_result': expected_result,
                    'priority': priority if priority in ['high', 'medium', 'low'] else 'medium',
                    'status': 'pending',
                    'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                testcases.append(new_case)

            save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

            return jsonify({'success': True, 'data': {'count': len(df)}})
        except ImportError:
            # 如果没有pandas，返回模拟成功
            return jsonify({'success': True, 'data': {'count': 0, 'message': '请安装pandas库支持Excel导入'}})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 图片识别 API ====================

# UI元素类型及其特征关键词映射
UI_ELEMENTS = {
    '输入框': {
        'keywords': ['用户名', '账号', '密码', '手机', '邮箱', '电话', '地址', '姓名', '内容', '搜索', '查询', '关键字', '验证码', '确认密码', '新密码', '旧密码'],
        'patterns': ['input', 'text', 'field'],
        'context': ['请输入', '请填写', '输入', '填写']
    },
    '密码框': {
        'keywords': ['密码', 'passwd', 'password'],
        'patterns': ['password'],
        'context': ['请输入密码', '密码']
    },
    '按钮': {
        'keywords': ['登录', '注册', '提交', '确定', '保存', '确认', '发送', '修改', '删除', '重置', '取消', '返回', '上一步', '下一步', '完成', '查询', '搜索', '提交'],
        'patterns': ['button', 'btn'],
        'context': []
    },
    '下拉框': {
        'keywords': ['选择', '省', '市', '区', '类型', '分类', '状态', '角色', '权限', '选项', '请选择'],
        'patterns': ['select', 'dropdown', 'combobox'],
        'context': ['请选择', '选择']
    },
    '复选框': {
        'keywords': ['同意', '记住', '选中', '订阅', '协议', '已读', '已同意', '我已阅读'],
        'patterns': ['checkbox', 'check'],
        'context': []
    },
    '单选框': {
        'keywords': ['性别', '男', '女', '是', '否', '类型'],
        'patterns': ['radio'],
        'context': []
    },
    '链接文本': {
        'keywords': ['查看', '详情', '更多', '跳转', '进入', '查看详情', '了解更多', '注册', '登录', '忘记密码', '返回'],
        'patterns': ['link', 'a'],
        'context': []
    },
    '上传区域': {
        'keywords': ['上传', '附件', '文件', '图片', '头像', '选择文件'],
        'patterns': ['upload', 'file'],
        'context': ['上传', '选择文件']
    },
    '表格': {
        'keywords': ['列表', '数据', '记录', '详情', '明细', '编号', '操作'],
        'patterns': ['table', 'grid'],
        'context': []
    },
    '分页': {
        'keywords': ['页', '上一页', '下一页', '第一页', '最后一页', '上页', '下页'],
        'patterns': ['pagination', 'page'],
        'context': []
    },
    'Tab标签': {
        'keywords': ['标签', 'tab', '切换', '首页', '个人中心', '设置', '我的', '订单'],
        'patterns': ['tab'],
        'context': []
    },
    '搜索框': {
        'keywords': ['搜索', '查询', '请搜索', '请输入关键词', '关键字'],
        'patterns': ['search'],
        'context': ['搜索', '查询']
    },
}

# 功能关键词映射
FUNCTION_KEYWORDS = {
    '登录': ['登录', '登陆', 'sign in', 'login'],
    '注册': ['注册', 'signup', 'register'],
    '查询': ['查询', '搜索', '搜索', 'search', 'find'],
    '新增': ['新增', '添加', '创建', '新建', 'add'],
    '修改': ['修改', '编辑', '更新', 'edit', 'update'],
    '删除': ['删除', '移除', 'remove'],
    '保存': ['保存', '存储', 'save'],
    '提交': ['提交', '发送', 'submit'],
    '重置': ['重置', '清空', 'reset', 'clear'],
    '导入': ['导入', 'import'],
    '导出': ['导出', 'export', '下载', 'download'],
    '审核': ['审核', '审批', 'review'],
    '分配': ['分配', '指派', 'assign'],
    '启用禁用': ['启用', '禁用', '开启', '关闭', 'enable', 'disable'],
    '排序': ['排序', '正序', '倒序', 'sort'],
    '筛选': ['筛选', '过滤', 'filter'],
    '分页': ['分页', 'page'],
    '校验': ['验证', '校验', '检查', 'validate'],
}

# 测试用例生成策略
TEST_CASE_STRATEGIES = [
    # 正向用例 - 正常情况
    {
        'type': '正向',
        'name_template': '{func}功能-正常{element}验证',
        'desc_template': '验证{func}功能在正常输入情况下的行为',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '输入有效的{element}数据', 'expected': '输入成功'},
            {'action': '点击{button}按钮', 'expected': '操作执行成功'},
            {'action': '验证结果', 'expected': '操作成功完成'}
        ],
        'priority': 'high'
    },
    # 反向用例 - 异常输入
    {
        'type': '反向',
        'name_template': '{func}功能-无效{element}验证',
        'desc_template': '验证{func}功能在无效输入时的错误处理',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '输入无效的{element}数据', 'expected': '输入成功'},
            {'action': '点击{button}按钮', 'expected': '显示错误提示'},
            {'action': '验证错误处理', 'expected': '错误提示信息正确'}
        ],
        'priority': 'high'
    },
    # 反向用例 - 空值
    {
        'type': '反向',
        'name_template': '{func}功能-空{element}验证',
        'desc_template': '验证{func}功能在{element}为空时的处理',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '不输入{element}数据', 'expected': '保持为空'},
            {'action': '点击{button}按钮', 'expected': '提示{element}不能为空'},
            {'action': '验证必填校验', 'expected': '校验提示正确'}
        ],
        'priority': 'high'
    },
    # 边界值 - 最大长度
    {
        'type': '边界值',
        'name_template': '{func}功能-{element}最大长度验证',
        'desc_template': '验证{element}输入最大长度时的处理',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '输入超长{element}数据', 'expected': '输入成功或被截断'},
            {'action': '点击{button}按钮', 'expected': '正常处理或提示过长'},
            {'action': '验证长度校验', 'expected': '长度限制生效'}
        ],
        'priority': 'medium'
    },
    # 边界值 - 特殊字符
    {
        'type': '边界值',
        'name_template': '{func}功能-{element}特殊字符验证',
        'desc_template': '验证{element}输入特殊字符时的处理',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '输入特殊字符如<>{{}}[]', 'expected': '输入成功'},
            {'action': '点击{button}按钮', 'expected': '正常处理或转义'},
            {'action': '验证特殊字符处理', 'expected': '无XSS等安全问题'}
        ],
        'priority': 'medium'
    },
    # 边界值 - 空格
    {
        'type': '边界值',
        'name_template': '{func}功能-{element}首尾空格验证',
        'desc_template': '验证{element}首尾空格的自动处理',
        'steps_template': [
            {'action': '进入{func}页面', 'expected': '页面加载正常'},
            {'action': '输入带首尾空格的{element}', 'expected': '输入成功'},
            {'action': '点击{button}按钮', 'expected': '正常处理'},
            {'action': '验证空格处理', 'expected': '空格被正确处理'}
        ],
        'priority': 'low'
    },
]


def recognize_ui_elements(text):
    """识别文本中的UI元素"""
    found_elements = []
    text_lower = text.lower()

    for element_type, element_info in UI_ELEMENTS.items():
        keywords = element_info.get('keywords', [])

        # 查找该元素类型的所有关键词
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # 检查是否已经在列表中
                existing = [e for e in found_elements if e['keyword'] == keyword]
                if not existing:
                    found_elements.append({
                        'type': element_type,
                        'keyword': keyword,
                        'context': keyword
                    })

    return found_elements


def recognize_functions(text):
    """识别文本中的功能"""
    found_functions = []

    for func_name, keywords in FUNCTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found_functions.append(func_name)
                break

    return list(set(found_functions))


def generate_test_cases(functions, elements, module_name):
    """根据识别的功能和元素生成全面测试用例"""
    generated_cases = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 如果没有识别到功能，生成通用功能
    if not functions:
        functions = ['通用功能']

    # 如果没有识别到元素，默认为输入框
    if not elements:
        elements = [{'type': '输入框', 'keyword': '内容', 'context': '内容'}]

    # 按元素类型分组
    elements_by_type = {}
    for el in elements:
        el_type = el.get('type', '输入框')
        if el_type not in elements_by_type:
            elements_by_type[el_type] = []
        elements_by_type[el_type].append(el)

    # 获取页面中识别到的按钮
    button_elements = elements_by_type.get('按钮', [])
    if not button_elements:
        # 如果没有识别到按钮，尝试从链接文本中获取
        button_elements = elements_by_type.get('链接文本', [])
    default_button = button_elements[0].get('keyword', '确定') if button_elements else '确定'

    # 根据元素类型定义不同的测试策略
    element_test_strategies = {
        '输入框': [
            {'type': '正向', 'name': '{element}正向-有效输入', 'desc': '验证{element}输入有效数据', 'priority': 'high'},
            {'type': '正向', 'name': '{element}正向-正常长度', 'desc': '验证{element}输入正常长度数据', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-空值校验', 'desc': '验证{element}为空时的校验', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-无效格式', 'desc': '验证{element}输入无效格式数据', 'priority': 'high'},
            {'type': '边界值', 'name': '{element}边界-最大长度', 'desc': '验证{element}输入最大长度', 'priority': 'medium'},
            {'type': '边界值', 'name': '{element}边界-超长输入', 'desc': '验证{element}输入超长数据', 'priority': 'medium'},
            {'type': '边界值', 'name': '{element}边界-特殊字符', 'desc': '验证{element}输入特殊字符', 'priority': 'medium'},
            {'type': '边界值', 'name': '{element}边界-首尾空格', 'desc': '验证{element}首尾空格处理', 'priority': 'low'},
        ],
        '密码框': [
            {'type': '正向', 'name': '{element}正向-正确密码', 'desc': '验证{element}输入正确密码', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-错误密码', 'desc': '验证{element}输入错误密码', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-空密码', 'desc': '验证{element}为空时的校验', 'priority': 'high'},
            {'type': '边界值', 'name': '{element}边界-密码强度', 'desc': '验证{element}密码强度要求', 'priority': 'medium'},
        ],
        '按钮': [
            {'type': '正向', 'name': '{element}正向-正常点击', 'desc': '验证{element}正常点击', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-连续点击', 'desc': '验证{element}连续点击处理', 'priority': 'medium'},
            {'type': '边界值', 'name': '{element}边界-快速点击', 'desc': '验证{element}快速连续点击', 'priority': 'low'},
        ],
        '下拉框': [
            {'type': '正向', 'name': '{element}正向-选择选项', 'desc': '验证{element}选择有效选项', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-未选择', 'desc': '验证{element}未选择时的校验', 'priority': 'high'},
            {'type': '正向', 'name': '{element}正向-默认选项', 'desc': '验证{element}默认选项显示', 'priority': 'medium'},
        ],
        '复选框': [
            {'type': '正向', 'name': '{element}正向-勾选', 'desc': '验证{element}勾选', 'priority': 'high'},
            {'type': '正向', 'name': '{element}正向-取消勾选', 'desc': '验证{element}取消勾选', 'priority': 'high'},
        ],
        '单选框': [
            {'type': '正向', 'name': '{element}正向-选择选项', 'desc': '验证{element}选择选项', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-重复选择', 'desc': '验证{element}重复选择', 'priority': 'low'},
        ],
        '链接文本': [
            {'type': '正向', 'name': '{element}正向-点击跳转', 'desc': '验证{element}点击跳转', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-无效链接', 'desc': '验证{element}无效链接处理', 'priority': 'medium'},
        ],
        '搜索框': [
            {'type': '正向', 'name': '{element}正向-有效关键词', 'desc': '验证{element}搜索有效关键词', 'priority': 'high'},
            {'type': '正向', 'name': '{element}正向-空格搜索', 'desc': '验证{element}空格搜索', 'priority': 'medium'},
            {'type': '反向', 'name': '{element}反向-空搜索', 'desc': '验证{element}空搜索', 'priority': 'high'},
            {'type': '边界值', 'name': '{element}边界-特殊字符', 'desc': '验证{element}特殊字符搜索', 'priority': 'medium'},
        ],
        '上传区域': [
            {'type': '正向', 'name': '{element}正向-上传文件', 'desc': '验证{element}上传文件', 'priority': 'high'},
            {'type': '反向', 'name': '{element}反向-上传大文件', 'desc': '验证{element}上传超大文件', 'priority': 'medium'},
            {'type': '反向', 'name': '{element}反向-上传无效文件', 'desc': '验证{element}上传无效文件', 'priority': 'medium'},
        ],
    }

    # 为每个元素生成测试用例
    for element in elements:
        element_type = element.get('type', '输入框')
        element_name = element.get('keyword', '内容')

        # 获取该元素类型的测试策略
        strategies = element_test_strategies.get(element_type, element_test_strategies.get('输入框', []))

        for strategy in strategies:
            # 确定按钮
            button = default_button

            # 根据元素类型确定预期结果
            result_map = {
                '输入框': '输入成功，验证通过',
                '密码框': '密码验证成功',
                '按钮': '点击成功，响应正常',
                '下拉框': '选项选择成功',
                '复选框': '状态切换成功',
                '单选框': '选项选择成功',
                '链接文本': '链接跳转成功',
                '搜索框': '搜索成功，返回结果',
                '上传区域': '上传成功',
            }
            result = result_map.get(element_type, '操作成功')

            # 构建测试步骤
            steps = build_test_steps(element_type, element_name, button, strategy['type'])

            case = {
                'id': str(uuid.uuid4()),
                'name': strategy['name'].format(element=element_name),
                'type': 'functional',
                'module': module_name,
                'description': strategy['desc'].format(element=element_name),
                'steps': steps,
                'expected_result': result,
                'priority': strategy['priority'],
                'status': 'pending',
                'test_category': strategy['type'],
                'recognized_element': element_name,
                'element_type': element_type,
                'created_at': now,
                'updated_at': now
            }
            generated_cases.append(case)

    # 如果没有识别到任何元素，生成通用测试用例
    if not generated_cases:
        for func in functions:
            for strategy in TEST_CASE_STRATEGIES:
                case_name = strategy['name_template'].format(func=func, element='内容', button=default_button)
                case_desc = strategy['desc_template'].format(func=func, element='内容')

                steps = []
                for step in strategy['steps_template']:
                    action = step['action'].format(func=func, element='内容', button=default_button)
                    expected = step['expected'].format(func=func, element='内容', button=default_button)
                    steps.append({'action': action, 'expected': expected})

                case = {
                    'id': str(uuid.uuid4()),
                    'name': case_name,
                    'type': 'functional',
                    'module': module_name,
                    'description': case_desc,
                    'steps': steps,
                    'expected_result': '操作成功',
                    'priority': strategy['priority'],
                    'status': 'pending',
                    'test_category': strategy['type'],
                    'created_at': now,
                    'updated_at': now
                }
                generated_cases.append(case)

    return generated_cases


def build_test_steps(element_type, element_name, button, test_type):
    """根据元素类型和测试类型构建测试步骤"""
    steps_map = {
        '输入框': {
            '正向': [
                {'action': f'定位{element_name}输入框', 'expected': '元素可见可交互'},
                {'action': f'在{element_name}输入框中输入有效数据', 'expected': '输入成功'},
                {'action': f'点击{button}按钮', 'expected': '操作执行成功'},
                {'action': '验证操作结果', 'expected': '验证通过'}
            ],
            '反向': [
                {'action': f'定位{element_name}输入框', 'expected': '元素可见可交互'},
                {'action': f'清空{element_name}输入框', 'expected': '输入框已清空'},
                {'action': f'点击{button}按钮', 'expected': '显示必填提示'},
                {'action': '验证提示信息', 'expected': '提示信息正确'}
            ],
            '边界值': [
                {'action': f'定位{element_name}输入框', 'expected': '元素可见可交互'},
                {'action': f'在{element_name}输入框中输入超长数据', 'expected': '输入成功或被截断'},
                {'action': f'点击{button}按钮', 'expected': '显示长度超限提示'},
                {'action': '验证长度校验', 'expected': '长度限制生效'}
            ]
        },
        '密码框': {
            '正向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可交互'},
                {'action': f'输入正确的密码', 'expected': '输入成功'},
                {'action': f'点击{button}按钮', 'expected': '登录成功'},
                {'action': '验证登录结果', 'expected': '验证通过'}
            ],
            '反向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可交互'},
                {'action': f'输入错误的密码', 'expected': '输入成功'},
                {'action': f'点击{button}按钮', 'expected': '显示密码错误提示'},
                {'action': '验证错误提示', 'expected': '提示信息正确'}
            ]
        },
        '按钮': {
            '正向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可点击'},
                {'action': f'点击{element_name}', 'expected': '点击成功'},
                {'action': '验证响应结果', 'expected': '响应正常'}
            ],
            '反向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可点击'},
                {'action': f'快速连续点击{element_name}两次', 'expected': '防止重复提交'},
                {'action': '验证防重复机制', 'expected': '只执行一次'}
            ]
        },
        '下拉框': {
            '正向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可交互'},
                {'action': f'点击{element_name}展开下拉选项', 'expected': '下拉框展开'},
                {'action': f'选择下拉选项', 'expected': '选项选中'},
                {'action': '验证选中结果', 'expected': '选中成功'}
            ],
            '反向': [
                {'action': f'定位{element_name}', 'expected': '元素可见可交互'},
                {'action': f'不选择任何选项，直接点击{button}', 'expected': '显示必填提示'},
                {'action': '验证必填校验', 'expected': '校验提示正确'}
            ]
        },
        '复选框': {
            '正向': [
                {'action': f'定位{element_name}复选框', 'expected': '复选框可见'},
                {'action': f'点击勾选{element_name}', 'expected': '复选框被勾选'},
                {'action': '验证勾选状态', 'expected': '状态为已勾选'}
            ]
        },
        '链接文本': {
            '正向': [
                {'action': f'定位{element_name}链接', 'expected': '链接可见可点击'},
                {'action': f'点击{element_name}链接', 'expected': '页面跳转成功'},
                {'action': '验证跳转结果', 'expected': '跳转正确'}
            ]
        },
        '搜索框': {
            '正向': [
                {'action': f'定位{element_name}', 'expected': '搜索框可见可交互'},
                {'action': f'在搜索框输入关键词', 'expected': '输入成功'},
                {'action': f'点击搜索按钮或按回车', 'expected': '搜索执行'},
                {'action': '验证搜索结果', 'expected': '返回相关结果'}
            ],
            '反向': [
                {'action': f'定位{element_name}', 'expected': '搜索框可见可交互'},
                {'action': f'不输入关键词，直接搜索', 'expected': '显示提示或显示全部'},
                {'action': '验证空搜索处理', 'expected': '处理正确'}
            ]
        },
        '上传区域': {
            '正向': [
                {'action': f'定位{element_name}', 'expected': '上传区域可见'},
                {'action': f'点击上传按钮并选择文件', 'expected': '文件选择成功'},
                {'action': f'点击上传确认', 'expected': '上传执行'},
                {'action': '验证上传结果', 'expected': '上传成功'}
            ],
            '反向': [
                {'action': f'定位{element_name}', 'expected': '上传区域可见'},
                {'action': f'尝试上传超大文件', 'expected': '显示文件过大提示'},
                {'action': '验证大小限制', 'expected': '大小限制生效'}
            ]
        }
    }

    # 返回对应类型的步骤，如果没有则返回默认步骤
    default_steps = [
        {'action': f'定位{element_name}', 'expected': '元素可见可交互'},
        {'action': f'执行操作', 'expected': '操作成功'},
        {'action': '验证结果', 'expected': '验证通过'}
    ]

    return steps_map.get(element_type, {}).get(test_type, default_steps)


@app.route('/api/functional/recognize-image', methods=['POST'])
def recognize_image():
    """通过图片识别生成测试用例"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请选择图片文件'}), 400

    image = request.files['image']
    if not image.filename:
        return jsonify({'success': False, 'message': '请选择图片文件'}), 400

    try:
        # 保存上传的图片
        upload_dir = os.path.join(DATA_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{image.filename}")
        image.save(image_path)

        # 读取图片并尝试识别
        recognized_text = ""
        try:
            from PIL import Image
            import pytesseract

            # 使用OCR识别图片中的文字
            recognized_text = pytesseract.image_to_string(Image.open(image_path), lang='chi_sim+eng')
        except Exception as e:
            # 如果OCR失败，使用占位符
            recognized_text = f"图片识别失败，使用默认模式生成测试用例"

        # 识别UI元素和功能
        elements = recognize_ui_elements(recognized_text)
        functions = recognize_functions(recognized_text)

        # 确定模块名称
        if functions:
            module_name = functions[0]
        else:
            module_name = 'UI功能'

        # 生成全面的测试用例
        testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
        generated_cases = generate_test_cases(functions, elements, module_name)

        if generated_cases:
            testcases.extend(generated_cases)
            save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

            # 统计各类用例数量
            category_stats = {}
            for case in generated_cases:
                cat = case.get('test_category', '未知')
                category_stats[cat] = category_stats.get(cat, 0) + 1

            stats_text = f"正向:{category_stats.get('正向', 0)}, 反向:{category_stats.get('反向', 0)}, 边界值:{category_stats.get('边界值', 0)}"

            return jsonify({
                'success': True,
                'data': {
                    'count': len(generated_cases),
                    'recognized_text': recognized_text[:200] if recognized_text else '未识别到文字',
                    'recognized_functions': functions,
                    'recognized_elements': [e['type'] for e in elements],
                    'category_stats': category_stats,
                    'message': f"识别到功能: {', '.join(functions) if functions else '通用'}, 元素: {', '.join([e['type'] for e in elements]) if elements else '默认'}, 生成测试用例: {stats_text}"
                }
            })
        else:
            # 生成通用测试用例
            generated_cases = generate_test_cases(['通用功能'], [{'type': '输入框', 'keyword': '内容', 'context': '内容'}], 'UI功能')
            testcases.extend(generated_cases)
            save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)
            return jsonify({
                'success': True,
                'data': {
                    'count': len(generated_cases),
                    'message': '已生成通用测试用例'
                }
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 手动生成测试用例 API ====================

@app.route('/api/functional/generate-manual', methods=['POST'])
def generate_from_manual():
    """手动输入页面元素生成测试用例"""
    data = request.json
    elements_text = data.get('elements', '')
    module_name = data.get('module', 'UI功能')

    if not elements_text:
        return jsonify({'success': False, 'message': '请输入页面元素'}), 400

    try:
        # 解析元素列表
        element_list = [e.strip() for e in elements_text.split(',') if e.strip()]

        # 将手动输入的元素转换为元素对象
        elements = []
        for elem in element_list:
            # 根据关键词判断元素类型
            elem_type = '输入框'  # 默认
            if any(kw in elem for kw in ['按钮', '登录', '注册', '提交', '确定', '保存']):
                elem_type = '按钮'
            elif any(kw in elem for kw in ['密码', 'passwd']):
                elem_type = '密码框'
            elif any(kw in elem for kw in ['选择', '下拉']):
                elem_type = '下拉框'
            elif any(kw in elem for kw in ['复选框', '同意', '记住']):
                elem_type = '复选框'
            elif any(kw in elem for kw in ['单选', '性别']):
                elem_type = '单选框'
            elif any(kw in elem for kw in ['链接', '查看', '详情']):
                elem_type = '链接文本'
            elif any(kw in elem for kw in ['搜索', '查询']):
                elem_type = '搜索框'
            elif any(kw in elem for kw in ['上传', '附件']):
                elem_type = '上传区域'

            elements.append({
                'type': elem_type,
                'keyword': elem,
                'context': elem
            })

        # 识别功能
        functions = recognize_functions(elements_text)
        if not functions:
            functions = [module_name]

        # 生成测试用例
        testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
        generated_cases = generate_test_cases(functions, elements, module_name)

        if generated_cases:
            testcases.extend(generated_cases)
            save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

            # 统计各类用例数量
            category_stats = {}
            for case in generated_cases:
                cat = case.get('test_category', '未知')
                category_stats[cat] = category_stats.get(cat, 0) + 1

            return jsonify({
                'success': True,
                'data': {
                    'count': len(generated_cases),
                    'recognized_elements': [e['keyword'] for e in elements],
                    'recognized_types': [e['type'] for e in elements],
                    'category_stats': category_stats,
                    'message': f"识别到 {len(elements)} 个元素，生成 {len(generated_cases)} 个测试用例（正向:{category_stats.get('正向', 0)}, 反向:{category_stats.get('反向', 0)}, 边界值:{category_stats.get('边界值', 0)}）"
                }
            })
        else:
            return jsonify({'success': False, 'message': '未能生成测试用例'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/functional/cases/batch', methods=['POST'])
def batch_create_functional_cases():
    """批量创建功能测试用例（用于AI生成结果保存）"""
    print(f"[DEBUG BATCH] request.json = {request.json}")
    data = request.json
    if not data or 'cases' not in data:
        print(f"[DEBUG BATCH] 400 - data={data}, 'cases' in data={'cases' in data if data else 'N/A'}")
        return jsonify({'success': False, 'message': '请提供测试用例数据'}), 400

    new_cases = data.get('cases', [])
    if not new_cases:
        # 空列表也返回成功，避免前端报错
        return jsonify({'success': True, 'data': {'count': 0}})

    def convert_steps_to_text(steps):
        """将步骤从JSON数组格式转换为文本格式"""
        if not steps:
            return ''
        if isinstance(steps, str):
            return steps
        if isinstance(steps, list):
            steps_text = ""
            for idx, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    action = step.get('action', '')
                    expected = step.get('expected', '')
                    steps_text += f"{idx}. {action}\n   预期：{expected}\n"
                else:
                    steps_text += f"{idx}. {step}\n"
            return steps_text.strip()
        return str(steps)

    try:
        testcases = load_json(os.path.join(DATA_DIR, 'functional_testcases.json'))
        existing_ids = {case['id'] for case in testcases}

        added_count = 0
        for case in new_cases:
            case_id = case.get('id')
            # 生成唯一ID
            if not case_id or case_id in existing_ids:
                case_id = str(uuid.uuid4())

            # 转换步骤为文本格式
            steps = case.get('steps', [])
            steps_text = convert_steps_to_text(steps)

            new_case = {
                'id': case_id,
                'name': case.get('name', case.get('case_name', '未命名用例')),
                'type': 'functional',
                'description': case.get('description', ''),
                'priority': case.get('priority', 'medium'),
                'steps': steps_text,
                'expected_result': case.get('expected_result', ''),
                'requirement_title': case.get('requirement_title', ''),
                'test_data': case.get('test_data', {}),
                'status': 'pending',
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            testcases.append(new_case)
            existing_ids.add(case_id)
            added_count += 1

        save_json(os.path.join(DATA_DIR, 'functional_testcases.json'), testcases)

        return jsonify({
            'success': True,
            'data': {
                'count': added_count
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 测试用例自动生成 API ====================

@app.route('/api/testcases/generate', methods=['POST'])
def generate_testcases():
    """AI自动生成测试用例"""
    data = request.json
    description = data.get('description', '')
    test_type = data.get('type', 'api')  # api 或 webui

    try:
        generated = test_generator.generate(description, test_type)

        # 保存生成的测试用例
        testcases = load_json(os.path.join(DATA_DIR, 'testcases.json'))
        testcases.extend(generated)
        save_json(os.path.join(DATA_DIR, 'testcases.json'), testcases)

        return jsonify({'success': True, 'data': generated})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 测试执行 API ====================

@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    """执行测试用例"""
    data = request.json
    case_ids = data.get('case_ids', [])

    try:
        results = test_executor.run(case_ids)

        # 保存执行结果
        results_file = os.path.join(DATA_DIR, 'test_results.json')
        all_results = load_json(results_file)
        all_results.extend(results)
        save_json(results_file, all_results)

        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/tests/run-all', methods=['POST'])
def run_all_tests():
    """执行所有测试用例"""
    try:
        results = test_executor.run_all()

        # 保存执行结果
        results_file = os.path.join(DATA_DIR, 'test_results.json')
        all_results = load_json(results_file)
        all_results.extend(results)
        save_json(results_file, all_results)

        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 测试报告 API ====================

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """获取测试报告（支持分页）"""
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(REPORTS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)
                reports.append(report)

    # 按时间倒序排列
    reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = reports[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """生成测试报告"""
    data = request.json
    result_ids = data.get('result_ids', [])

    try:
        report = report_generator.generate(result_ids)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/reports/<report_id>/download', methods=['GET'])
def download_report(report_id):
    """下载测试报告"""
    filepath = os.path.join(REPORTS_DIR, f'{report_id}.json')
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='application/json')
    return jsonify({'success': False, 'message': '报告不存在'}), 404


# ==================== 测试结果查询 API ====================

@app.route('/api/results', methods=['GET'])
def get_results():
    """获取功能测试执行结果（支持分页）"""
    results = load_json(os.path.join(DATA_DIR, 'test_results.json'))

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = results[start:end]

    return jsonify({
        'success': True,
        'data': paginated,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    })


@app.route('/api/results/clear', methods=['POST'])
def clear_results():
    """清空测试执行结果"""
    try:
        save_json(os.path.join(DATA_DIR, 'test_results.json'), [])
        return jsonify({'success': True, 'message': '执行记录已清空'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 根路径 ====================

@app.route('/')
def index():
    """返回前端页面"""
    return send_file(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html'))


# ==================== Bug报告生成 ====================

@app.route('/api/bug-report/import', methods=['POST'])
def import_bug_file():
    """导入Bug Excel文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': '请上传Excel文件'}), 400

    try:
        from backend.defect_analyzer import DefectAnalyzer

        # 保存上传的文件
        upload_dir = os.path.join(DATA_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        bug_file_path = os.path.join(upload_dir, f"bugs_{uuid.uuid4()}_{file.filename}")
        file.save(bug_file_path)

        # 分析Bug数据
        analyzer = DefectAnalyzer()
        analyzer.load_excel(bug_file_path)
        summary = analyzer.get_summary()

        # 自动生成测试概况描述
        auto_overview = generate_auto_overview(summary)
        # 自动生成团队信息
        auto_team = generate_auto_team(summary)
        # 自动生成测试范围
        auto_test_scope = generate_auto_test_scope(summary)
        # 自动生成重点关注问题
        auto_focus_points = generate_auto_focus_points(summary)
        # 自动生成问题及风险
        auto_risks = generate_auto_risks(summary)

        # 格式化测试时间
        test_time_str = ''
        test_start = summary.get('test_start')
        test_end = summary.get('test_end')
        if test_start and test_end:
            try:
                # 尝试转换为日期格式
                if hasattr(test_start, 'strftime'):
                    start_str = test_start.strftime('%Y.%m.%d')
                else:
                    start_str = str(test_start)[:10]
                if hasattr(test_end, 'strftime'):
                    end_str = test_end.strftime('%Y.%m.%d')
                else:
                    end_str = str(test_end)[:10]
                test_time_str = f"{start_str}—{end_str}"
            except:
                test_time_str = f"{test_start}—{test_end}"
        elif test_start:
            try:
                if hasattr(test_start, 'strftime'):
                    test_time_str = test_start.strftime('%Y.%m.%d')
                else:
                    test_time_str = str(test_start)[:10]
            except:
                test_time_str = str(test_start)

        return jsonify({
            'success': True,
            'data': {
                'file_path': bug_file_path,
                'total': summary['total'],
                'by_category': summary['by_category'],
                'by_severity': summary['by_severity'],
                'by_handler': summary['by_handler'],
                'by_status': summary['by_status'],
                'by_verifier': summary.get('by_verifier', {}),
                'by_reason': summary.get('by_reason', {}),
                'handlers_list': summary.get('handlers_list', []),
                'verifiers': summary.get('verifiers', []),
                'all_titles': summary.get('all_titles', []),  # 返回完整的bug标题列表供AI分析使用
                'auto_overview': auto_overview,
                'auto_team': auto_team,
                'auto_test_scope': auto_test_scope,
                'auto_focus_points': auto_focus_points,
                'auto_risks': auto_risks,
                'test_time': test_time_str,
                'version': summary.get('version', '')
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def generate_auto_overview(summary):
    """根据Bug统计数据自动生成测试概况描述（约300字）"""
    total = summary.get('total', 0)
    by_category = summary.get('by_category', {})
    by_severity = summary.get('by_severity', {})
    by_status = summary.get('by_status', {})
    by_reason = summary.get('by_reason', {})
    defect_list = summary.get('all_titles', [])[:10]  # 取前10条Bug标题

    # 构建描述
    parts = []

    # 整体评价
    if total <= 10:
        parts.append(f"本版本整体提测质量良好，共发现{total}个Bug，整体质量可控。")
    elif total <= 30:
        parts.append(f"本版本整体提测质量一般，共发现{total}个Bug，存在一定数量的缺陷需要修复。")
    else:
        parts.append(f"本版本整体提测质量有待提升，共发现{total}个Bug，需重点关注和修复。")

    # Bug类型分析
    if by_category:
        category_strs = [f"{k}{v}个" for k, v in list(by_category.items())[:3]]
        if category_strs:
            parts.append(f"从缺陷类型分布来看，{','.join(category_strs)}为主要问题类型。")

    # 严重程度分析
    severe_count = by_severity.get('严重', 0) + by_severity.get('致命', 0)
    high_count = by_severity.get('高', 0)
    if severe_count > 0:
        parts.append(f"其中{severe_count}个严重及以上级别Bug需优先处理，{high_count}个高级别Bug需重点关注。")
    else:
        parts.append("未发现严重及以上级别Bug，整体质量风险较低。")

    # 状态分析
    closed_count = by_status.get('已关闭', 0)
    resolved_count = by_status.get('已解决', 0) + by_status.get('待验收', 0)
    if closed_count > 0 and total > 0:
        closed_rate = closed_count / total * 100
        parts.append(f"截止目前，已关闭{closed_count}个Bug，关闭率{closed_rate:.1f}%，已解决{resolved_count}个待验收。")

    # 缺陷原因分类分析
    if by_reason:
        reason_strs = [f"{k}{v}个" for k, v in list(by_reason.items())[:3]]
        if reason_strs:
            parts.append(f"从缺陷原因分类来看，{','.join(reason_strs)}为主要原因。")

    # 提取Bug标题关键词
    if defect_list:
        titles = [d.get('title', '') for d in defect_list if d.get('title')]
        if titles:
            # 取前3个标题的核心关键词
            keywords = []
            for title in titles[:3]:
                # 简单提取前10个字符作为关键词
                if len(title) > 10:
                    keywords.append(title[:10])
                else:
                    keywords.append(title)
            if keywords:
                parts.append(f"典型问题如：{'、'.join(keywords)}等。")

    # 组合描述
    overview = ''.join(parts)

    # 补充通用描述以达到约300字
    if len(overview) < 200:
        overview += "本次需求均已按照需求评审时的需求实现，提测的需求内容开发思维逻辑完整，原型还原度较高，全流程无断点和阻塞。但由于涉及的功能点较多较细，存在一些功能细节的忽略导致出现部分Bug，建议在后续迭代中加强细节测试。"

    # 如果还是不够长，再补充
    if len(overview) < 250:
        overview += "在测试过程中也发现了一些需求评审时未考虑到的个别细节问题，建议产品经理在后续需求评审时更加全面地考虑各种使用场景。"

    return overview


def generate_auto_test_scope(summary):
    """根据Bug数据自动生成测试范围"""
    import re
    defect_list = summary.get('all_titles', [])

    # 从Bug标题中提取【】里的内容作为测试范围
    scopes = set()

    for defect in defect_list[:50]:  # 分析前50条
        title = defect.get('title', '')
        module = defect.get('module', '')

        # 提取【】里的内容
        if title:
            bracket_contents = re.findall(r'【([^】]+)】', title)
            for content in bracket_contents:
                if content and len(content) < 20:  # 过滤太长的内容
                    scopes.add(content)

        # 提取模块信息
        if module:
            scopes.add(module)

    # 转换为列表
    scope_list = list(scopes)

    # 如果没有提取到足够的范围，从标题中提取功能关键词
    if len(scope_list) < 3:
        for defect in defect_list[:30]:
            title = defect.get('title', '')
            if title:
                # 常见功能关键词
                keywords = ['项目详情', '项目总结', '项目得分', '项目分析', '雷达图', '数据展示',
                           '导出功能', '新增亮点', '手动创建', '自动创建', '得分计算', '问题展示',
                           '风险展示', '自动闭环', '自动罗列', '报告', '图表', '配置', '权限']
                for kw in keywords:
                    if kw in title:
                        scopes.add(kw)
        scope_list = list(scopes)

    # 如果还是没有足够的范围，添加默认值
    if len(scope_list) < 3:
        scope_list = [
            '项目详情页的项目总结展示、项目得分展示',
            '项目智能分析报告的雷达图及数据展示',
            '项目各维度的得分逻辑和问题自动创建',
            '完整版项目分析报告的数据展示和导出功能'
        ]

    return scope_list


def generate_auto_focus_points(summary):
    """根据Bug数据自动生成需要重点关注的问题"""
    by_severity = summary.get('by_severity', {})
    by_category = summary.get('by_category', {})
    defect_list = summary.get('all_titles', [])

    focus_points = []

    # 根据严重程度添加重点关注
    severe_count = by_severity.get('严重', 0) + by_severity.get('致命', 0)
    high_count = by_severity.get('高', 0)

    if severe_count > 0 or high_count > 0:
        focus_points.append(f"重点关注严重和高级别Bug（共{severe_count + high_count}个）的修复和验证。")

    # 根据缺陷类型添加重点关注
    ui_bugs = by_category.get('界面问题', 0) + by_category.get('前端问题', 0)
    logic_bugs = by_category.get('逻辑问题', 0) + by_category.get('功能问题', 0)

    if ui_bugs > 0:
        focus_points.append(f"UI界面问题较多（{ui_bugs}个），需关注用户体验和原型还原度。")

    if logic_bugs > 0:
        focus_points.append(f"功能逻辑问题（{logic_bugs}个）需重点验证业务逻辑正确性。")

    # 从Bug标题中提取具体问题
    for defect in defect_list[:5]:
        title = defect.get('title', '')
        severity = defect.get('severity', '')
        if title and (severity in ['严重', '高', '致命']):
            # 截取标题前30个字符
            focus_point = title[:30] + '...' if len(title) > 30 else title
            if focus_point not in focus_points:
                focus_points.append(focus_point)

    # 如果没有提取到重点关注，添加默认项
    if not focus_points:
        focus_points = [
            "项目健康智能分析每天定时任务更新数据，需关注数据时效性",
            "上线前需提前同步线上数据库表结构变化、定时任务配置和权限配置等"
        ]

    return focus_points


def generate_auto_risks(summary):
    """根据Bug数据自动生成问题及风险"""
    total = summary.get('total', 0)
    by_status = summary.get('by_status', {})
    by_severity = summary.get('by_severity', {})
    defect_list = summary.get('all_titles', [])

    risks = []

    # 根据Bug状态分析风险
    open_count = by_status.get('打开', 0) + by_status.get('新建', 0) + by_status.get('待处理', 0)
    if open_count > 0:
        risks.append(f"仍有{open_count}个Bug未关闭，需持续跟进修复进度。")

    # 根据严重程度分析风险
    severe_count = by_severity.get('严重', 0) + by_severity.get('致命', 0)
    if severe_count > 0:
        risks.append(f"存在{severe_count}个严重级别Bug，可能影响系统稳定性和核心功能。")

    # 根据缺陷原因分类分析风险
    by_reason = summary.get('by_reason', {})
    if by_reason:
        top_reasons = list(by_reason.items())[:2]
        for reason, count in top_reasons:
            risks.append(f"因{reason}导致的Bug有{count}个，需在后续开发中加强注意。")

    # 从具体Bug中提取风险
    for defect in defect_list[:3]:
        title = defect.get('title', '')
        reason = defect.get('reason', '')
        if reason and len(reason) > 5:
            risk_point = f"关于{title[:20]}：{reason[:30]}"
            if risk_point not in risks:
                risks.append(risk_point)

    # 添加通用风险提示
    if len(risks) < 2:
        risks.append("由于项目健康智能分析数据是每天定时任务更新数据，可能会存在用户及时处理了项目如编制了项目计划、预算等，却看到分数和风险等数据未实时更新，需要和用户表明，是第二天定时任务更新数据，不是实时更新。")
        risks.append("本次需求功能均是在测试环境中测试实现，测试环境的数据是认为构造，待生产发布后，可能会有某个细节点的不一致，需要及时关注线上相关功能情况。")

    return risks


def generate_auto_team(summary):
    """根据Bug统计数据自动生成团队信息"""
    handlers = summary.get('handlers_list', [])
    verifiers = summary.get('verifiers', [])

    team = {}

    # 处理人作为开发人员
    if handlers:
        team['后端'] = '、'.join(handlers)
        team['前端'] = ''

    # 验证人作为测试人员
    if verifiers:
        team['测试'] = '、'.join(verifiers)

    return team


@app.route('/api/bug-report/generate', methods=['POST'])
def generate_bug_report():
    """生成Bug测试报告"""
    data = request.json
    bug_file_path = data.get('bug_file_path')
    project_name = data.get('project_name', 'EDSP-项目健康智能分析')

    if not bug_file_path:
        return jsonify({'success': False, 'message': '请先导入Bug文件'}), 400

    try:
        from backend.bug_report_generator import generate_test_report
        from backend.defect_analyzer import DefectAnalyzer
        from datetime import datetime
        import json

        # 生成报告文件（使用时间戳确保唯一性）
        report_dir = os.path.join(DATA_DIR, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_id = f"report_{timestamp}"
        report_file_path = os.path.join(report_dir, f"{project_name}质量测试报告_{timestamp}.docx")

        # 获取Bug统计数据
        analyzer = DefectAnalyzer()
        analyzer.load_excel(bug_file_path)
        summary = analyzer.get_summary()

        # 自动生成测试概况描述
        auto_overview = generate_auto_overview(summary)
        # 自动生成团队信息
        auto_team = generate_auto_team(summary)
        # 自动生成测试范围
        auto_test_scope = generate_auto_test_scope(summary)
        # 自动生成重点关注问题
        auto_focus_points = generate_auto_focus_points(summary)
        # 自动生成问题及风险
        auto_risks = generate_auto_risks(summary)

        # 如果有自定义配置
        config = {}
        if 'test_time' in data:
            config['test_time'] = data['test_time']
        if 'conclusion' in data:
            config['conclusion'] = data['conclusion']
        # 如果前端没有提供团队信息，使用自动生成的
        if 'team' in data and data['team']:
            config['team'] = data['team']
        else:
            config['team'] = auto_team
        # 如果前端没有提供测试范围，使用自动生成的
        if 'test_scope' in data and data['test_scope']:
            config['test_scope'] = data['test_scope']
        else:
            config['test_scope'] = auto_test_scope
        # 如果前端没有提供重点关注问题，使用自动生成的
        if 'focus_points' in data and data['focus_points']:
            config['focus_points'] = data['focus_points']
        else:
            config['focus_points'] = auto_focus_points
        # 如果前端没有提供问题及风险，使用自动生成的
        if 'risks' in data and data['risks']:
            config['risks'] = data['risks']
        else:
            config['risks'] = auto_risks
        # 如果前端没有提供概况描述，使用自动生成的
        if 'overview' in data and data['overview']:
            config['overview'] = data['overview']
        else:
            config['overview'] = auto_overview

        # 生成报告文件
        generate_test_report(bug_file_path, report_file_path, project_name, config)

        # 保存报告记录
        report_record = {
            'id': report_id,
            'project_name': project_name,
            'conclusion': data.get('conclusion', '测试通过，已达交付标准。'),
            'overview': data.get('overview', '本版本的整体提测质量优秀。'),
            'focus_points': data.get('focus_points', []),
            'risks': data.get('risks', []),
            'test_scope': data.get('test_scope', []),
            'test_time': data.get('test_time', ''),
            'team': data.get('team', {}),
            'test_device': '本轮测试所用浏览器：谷歌浏览器',
            'total_bugs': summary['total'],
            'by_category': summary['by_category'],
            'by_severity': summary['by_severity'],
            'by_handler': summary['by_handler'],
            'by_status': summary['by_status'],
            'defect_list': analyzer.get_defect_list()[:50],
            'file_path': os.path.basename(report_file_path),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 保存报告记录到JSON文件
        records_file = os.path.join(report_dir, 'report_records.json')
        records = []
        if os.path.exists(records_file):
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        records.insert(0, report_record)  # 新报告放在最前面
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'data': {
                'report_id': report_id,
                'report_path': report_file_path,
                'download_url': f'/api/bug-report/download?path={os.path.basename(report_file_path)}'
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug-report/download', methods=['GET'])
def download_bug_report():
    """下载生成的报告"""
    from urllib.parse import unquote
    report_name = request.args.get('path')
    if not report_name:
        return jsonify({'success': False, 'message': '请指定报告文件名'}), 400

    # URL 解码文件名
    report_name = unquote(report_name)

    # 直接路径检查
    report_path = os.path.join(DATA_DIR, 'reports', report_name)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=report_name)

    # 如果直接路径不存在，尝试在目录中模糊匹配
    reports_dir = os.path.join(DATA_DIR, 'reports')
    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            if f.endswith('.docx') and report_name.split('.docx')[0] in f:
                report_path = os.path.join(reports_dir, f)
                return send_file(report_path, as_attachment=True, download_name=f)

    return jsonify({'success': False, 'message': '报告文件不存在'}), 404


@app.route('/api/bug-report/preview', methods=['GET'])
def preview_bug_summary():
    """预览Bug统计摘要"""
    # 获取reports目录下最新的Bug文件
    upload_dir = os.path.join(DATA_DIR, 'uploads')
    if not os.path.exists(upload_dir):
        return jsonify({'success': True, 'data': {}})

    bug_files = [f for f in os.listdir(upload_dir) if f.startswith('bugs_') and f.endswith(('.xlsx', '.xls'))]
    if not bug_files:
        return jsonify({'success': True, 'data': {}})

    # 使用最新的Bug文件
    latest_file = os.path.join(upload_dir, sorted(bug_files)[-1])

    try:
        from backend.defect_analyzer import DefectAnalyzer
        analyzer = DefectAnalyzer()
        analyzer.load_excel(latest_file)
        summary = analyzer.get_summary()
        # 添加file_path到返回数据
        summary['file_path'] = latest_file

        # 自动生成测试概况描述
        summary['auto_overview'] = generate_auto_overview(summary)
        # 自动生成团队信息
        summary['auto_team'] = generate_auto_team(summary)
        # 自动生成测试范围
        summary['auto_test_scope'] = generate_auto_test_scope(summary)
        # 自动生成重点关注问题
        summary['auto_focus_points'] = generate_auto_focus_points(summary)
        # 自动生成问题及风险
        summary['auto_risks'] = generate_auto_risks(summary)

        # 格式化测试时间
        test_start = summary.get('test_start')
        test_end = summary.get('test_end')
        test_time_str = ''
        if test_start and test_end:
            try:
                if hasattr(test_start, 'strftime'):
                    start_str = test_start.strftime('%Y.%m.%d')
                else:
                    start_str = str(test_start)[:10]
                if hasattr(test_end, 'strftime'):
                    end_str = test_end.strftime('%Y.%m.%d')
                else:
                    end_str = str(test_end)[:10]
                test_time_str = f"{start_str}—{end_str}"
            except:
                test_time_str = f"{test_start}—{test_end}"
        summary['test_time'] = test_time_str
        # 添加版本号到返回数据
        if 'version' not in summary:
            summary['version'] = ''

        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug-report/list', methods=['GET'])
def list_bug_reports():
    """获取报告列表（支持分页）"""
    import json
    report_dir = os.path.join(DATA_DIR, 'reports')
    records_file = os.path.join(report_dir, 'report_records.json')

    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    if not os.path.exists(records_file):
        return jsonify({
            'success': True,
            'data': [],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': 0,
                'total_pages': 0
            }
        })

    try:
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)

        # 按创建时间倒序排序
        records.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # 计算分页
        total = len(records)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # 返回当前页的数据
        page_records = records[start_index:end_index]

        # 返回简化信息
        simple_records = []
        for r in page_records:
            simple_records.append({
                'id': r.get('id'),
                'project_name': r.get('project_name'),
                'total_bugs': r.get('total_bugs'),
                'conclusion': r.get('conclusion'),
                'created_at': r.get('created_at'),
                'file_path': r.get('file_path')
            })

        return jsonify({
            'success': True,
            'data': simple_records,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug-report/delete/<report_id>', methods=['DELETE'])
def delete_bug_report(report_id):
    """删除报告"""
    import json
    report_dir = os.path.join(DATA_DIR, 'reports')
    records_file = os.path.join(report_dir, 'report_records.json')

    if not os.path.exists(records_file):
        return jsonify({'success': False, 'message': '报告不存在'}), 404

    try:
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)

        # 找到要删除的报告
        report_to_delete = None
        for r in records:
            if r.get('id') == report_id:
                report_to_delete = r
                break

        if not report_to_delete:
            return jsonify({'success': False, 'message': '报告不存在'}), 404

        # 删除报告文件（如果存在）
        if report_to_delete.get('file_path'):
            file_path = report_to_delete['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)

        # 从记录中移除
        records = [r for r in records if r.get('id') != report_id]

        # 保存更新后的记录
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'message': '报告已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ai/analyze-bugs', methods=['POST'])
def analyze_bugs_with_ai():
    """使用大模型分析Bug数据，生成测试报告摘要"""
    data = request.json
    summary = data.get('summary', {})

    # 从请求中获取LLM配置（优先使用请求中的配置）
    provider = data.get('provider', 'minimax')
    api_key = data.get('api_key', '')
    group_id = data.get('group_id', '')
    use_local = data.get('use_local', False)

    if not api_key:
        return jsonify({'success': False, 'message': '请先配置LLM API密钥'}), 400

    try:
        # 准备Bug数据摘要
        if not isinstance(summary, dict):
            summary = {}
        total = summary.get('total', 0)
        by_category = summary.get('by_category', {}) if isinstance(summary.get('by_category'), dict) else {}
        by_severity = summary.get('by_severity', {}) if isinstance(summary.get('by_severity'), dict) else {}
        by_status = summary.get('by_status', {}) if isinstance(summary.get('by_status'), dict) else {}
        by_reason = summary.get('by_reason', {}) if isinstance(summary.get('by_reason'), dict) else {}
        defect_list = summary.get('all_titles', [])[:50]  # 最多50条
        version = summary.get('version', '未知版本')

        # 构建提示词
        defect_text = ""
        for d in defect_list[:30]:
            if not isinstance(d, dict):
                d = {}
            title = d.get('title', '')
            severity = d.get('severity', '')
            status = d.get('status', '')
            category = d.get('category', '')
            reason = d.get('reason', '')
            defect_text += f"- [{severity}] [{status}] [{category}] {title}"
            if reason:
                defect_text += f" (原因: {reason})"
            defect_text += "\n"

        prompt = f"""你是一位资深测试专家，请根据以下Bug数据为测试报告生成专业的分析摘要。

## 版本信息
{version}

## Bug统计数据
- 总Bug数: {total}
- 按严重程度: {', '.join([f'{k}:{v}个' for k,v in by_severity.items()]) if by_severity else '无数据'}
- 按状态: {', '.join([f'{k}:{v}个' for k,v in by_status.items()]) if by_status else '无数据'}
- 按类型: {', '.join([f'{k}:{v}个' for k,v in by_category.items()]) if by_category else '无数据'}
- 按原因: {', '.join([f'{k}:{v}个' for k,v in by_reason.items()]) if by_reason else '无数据'}

## 详细Bug列表（前30条）
{defect_text}

请生成以下4个部分的内容，每部分用换行分隔：

1. 测试概况描述（约200字）：整体评价、Bug分布特点、测试质量评估
2. 测试范围（每行一项）：从Bug中提取的功能模块和测试点
3. 需要重点关注问题（每行一项）：高严重级别Bug、待验收Bug等需要重点关注的问题
4. 问题及风险（每行一项）：潜在风险、未关闭Bug、可能影响

请用中文回答，格式如下：
[测试概况描述]
...
[测试范围]
功能点1
功能点2
...
[重点关注问题]
问题1
问题2
...
[问题及风险]
风险1
风险2
..."""

        # 调用LLM
        if provider == 'glm':
            from backend.glm_client import get_glm_client
            client = get_glm_client(api_key=api_key, local=use_local)
        else:
            from backend.minimax_client import get_minimax_client
            client = get_minimax_client(api_key=api_key, group_id=group_id, local=use_local)

        success, result = client.chat(
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )

        if not success:
            return jsonify({'success': False, 'message': f'LLM调用失败: {result}'}), 500

        # 解析返回内容
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '') if provider != 'minimax' else result.get('choices', [{}])[0].get('message', {}).get('content', '')
        if provider == 'minimax':
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
            elif 'messages' in result:
                content = result['messages'][-1].get('text', '') if result['messages'] else ''

        if not content:
            return jsonify({'success': False, 'message': 'LLM返回内容为空'}), 500

        # 解析生成的内容 - 使用更健壮的按行解析方式
        overview = ''
        scope = []
        focus = []
        risks = []

        content_lines = content.strip().split('\n')
        current_section = 'overview'
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            # 检测section标记
            if '测试概况描述' in line:
                current_section = 'overview'
                line = line.replace('[测试概况描述]', '').replace('测试概况描述', '').strip()
                if line:
                    overview += line + ' '
                continue
            elif '测试范围' in line and '重点' not in line:
                current_section = 'scope'
                line = line.replace('[测试范围]', '').replace('测试范围', '').strip()
                if line:
                    scope.append(line)
                continue
            elif '重点关注问题' in line or '需要重点关注' in line:
                current_section = 'focus'
                line = line.replace('[重点关注问题]', '').replace('[需要重点关注问题]', '').replace('重点关注问题', '').replace('需要重点关注', '').strip()
                if line:
                    focus.append(line)
                continue
            elif '问题及风险' in line or (current_section == 'focus' and '风险' in line):
                current_section = 'risks'
                line = line.replace('[问题及风险]', '').replace('问题及风险', '').strip()
                if line:
                    risks.append(line)
                continue
            # 根据当前section添加内容
            if current_section == 'overview':
                overview += line + ' '
            elif current_section == 'scope' and line:
                scope.append(line)
            elif current_section == 'focus' and line:
                focus.append(line)
            elif current_section == 'risks' and line:
                risks.append(line)

        overview = overview.strip()
        # 清理列表中的空项和纯数字项
        scope = [s for s in scope if s and not s.isdigit()]
        focus = [s for s in focus if s and not s.isdigit()]
        risks = [s for s in risks if s and not s.isdigit()]

        return jsonify({
            'success': True,
            'data': {
                'auto_overview': overview,
                'auto_test_scope': scope,
                'auto_focus_points': focus,
                'auto_risks': risks
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug-report/detail/<report_id>', methods=['GET'])
def get_bug_report_detail(report_id):
    """获取报告详情"""
    import json
    report_dir = os.path.join(DATA_DIR, 'reports')
    records_file = os.path.join(report_dir, 'report_records.json')

    if not os.path.exists(records_file):
        return jsonify({'success': False, 'message': '报告不存在'}), 404

    try:
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)

        for r in records:
            if r.get('id') == report_id:
                return jsonify({'success': True, 'data': r})

        return jsonify({'success': False, 'message': '报告不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 远程缺陷API ====================

@app.route('/api/bug-report/fetch-remote', methods=['POST'])
def fetch_remote_defects():
    """从远程API获取缺陷数据"""
    from backend.remote_defect_client import get_remote_client, get_cache

    data = request.json or {}
    version = data.get('version')
    token = data.get('token')  # 可选的自定义token
    use_cache = data.get('use_cache', True)

    # 获取项目ID
    project_id = os.getenv('EDSP_PROJECT_ID', '2007642735088656025')

    # 创建客户端
    client = get_remote_client(project_id=project_id, token=token)

    if not client.is_configured():
        return jsonify({
            'success': False,
            'message': '请提供有效的认证Token'
        }), 400

    # 尝试从缓存获取
    cache = get_cache(DATA_DIR)
    if use_cache and version:
        cached_data = cache.get(version)
        if cached_data:
            return jsonify({
                'success': True,
                'data': cached_data,
                'cached': True
            })

    # 从远程获取
    success, result = client.fetch_defects(version=version)

    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 502

    # 解析缺陷数据
    defects = client.parse_defects(result)

    # 获取统计信息
    statistics = client.get_statistics(defects)

    # 获取版本列表
    _, versions = client.fetch_versions()

    response_data = {
        'total': len(defects),
        'defects': defects,
        'statistics': statistics,
        'versions': versions,
        'project_id': project_id
    }

    # 缓存数据
    if use_cache and version:
        cache.set(version, response_data)

    return jsonify({
        'success': True,
        'data': response_data,
        'cached': False
    })


@app.route('/api/bug-report/versions', methods=['GET'])
def get_remote_versions():
    """获取远程项目的版本列表"""
    from backend.remote_defect_client import get_remote_client

    token = request.args.get('token')

    project_id = os.getenv('EDSP_PROJECT_ID', '2007642735088656025')
    client = get_remote_client(project_id=project_id, token=token)

    if not client.is_configured():
        return jsonify({
            'success': False,
            'message': '请提供有效的认证Token'
        }), 400

    success, versions = client.fetch_versions()

    if not success:
        return jsonify({
            'success': False,
            'message': '获取版本列表失败'
        }), 502

    return jsonify({
        'success': True,
        'data': versions
    })


@app.route('/api/bug-report/remote-config', methods=['POST'])
def set_remote_config():
    """设置远程API配置（Token等）"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': '请提供配置数据'}), 400

    token = data.get('token')
    project_id = data.get('project_id')

    if token:
        os.environ['EDSP_API_TOKEN'] = token
    if project_id:
        os.environ['EDSP_PROJECT_ID'] = project_id

    return jsonify({'success': True, 'message': '配置已更新'})


@app.route('/api/bug-report/generate-from-remote', methods=['POST'])
def generate_report_from_remote():
    """从远程数据生成测试报告"""
    from backend.bug_report_generator import BugReportGenerator

    data = request.json or {}
    version = data.get('version')
    token = data.get('token')
    config = data.get('config', {})

    # 获取缺陷数据
    from backend.remote_defect_client import get_remote_client, get_cache

    project_id = os.getenv('EDSP_PROJECT_ID', '2007642735088656025')
    client = get_remote_client(project_id=project_id, token=token)

    if not client.is_configured():
        return jsonify({
            'success': False,
            'message': '请提供有效的认证Token'
        }), 400

    success, result = client.fetch_defects(version=version)

    if not success:
        return jsonify({
            'success': False,
            'message': result
        }), 502

    # 解析缺陷数据
    defects = client.parse_defects(result)
    statistics = client.get_statistics(defects)

    # 准备报告数据
    report_data = {
        'project_name': config.get('project_name', 'EDSP-项目健康智能分析'),
        'conclusion': config.get('conclusion', '测试通过，已达交付标准。'),
        'overview': config.get('overview', '本版本的整体提测质量优秀。'),
        'focus_points': config.get('focus_points', []),
        'risks': config.get('risks', []),
        'test_scope': config.get('test_scope', []),
        'total_bugs': statistics['total'],
        'by_category': statistics['by_category'],
        'by_severity': statistics['by_severity'],
        'by_handler': statistics['by_handler'],
        'by_status': statistics['by_status'],
        'test_time': config.get('test_time', datetime.now().strftime('%Y.%m.%d')),
        'team': config.get('team', {}),
        'test_device': config.get('test_device', '本轮测试所用浏览器：谷歌浏览器'),
        'defect_list': defects
    }

    # 生成报告
    try:
        report_dir = os.path.join(DATA_DIR, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_str = f"_v{version[:8]}" if version else ""
        output_filename = f"测试报告{version_str}_{timestamp}.docx"
        output_path = os.path.join(report_dir, output_filename)

        generator = BugReportGenerator()
        generator.generate_report(report_data, output_path)

        # 保存记录
        save_report_record(report_data, output_path)

        return jsonify({
            'success': True,
            'data': {
                'file_path': output_filename,
                'total_bugs': statistics['total'],
                'statistics': statistics
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成报告失败: {str(e)}'
        }), 500


# ==================== Bug截图识别 API ====================

@app.route('/api/bug/recognize-screenshot', methods=['POST'])
def recognize_bug_screenshot():
    """通过AI识别截图中的bug信息"""
    from backend.bug_screenshot_recognizer import get_recognizer, get_storage

    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请选择图片文件'}), 400

    image = request.files['image']
    if not image.filename:
        return jsonify({'success': False, 'message': '请选择图片文件'}), 400

    # 检查文件大小 (10MB限制)
    image.seek(0, os.SEEK_END)
    file_size = image.tell()
    image.seek(0)
    if file_size > 10 * 1024 * 1024:
        return jsonify({'success': False, 'message': '图片大小不能超过10MB'}), 400

    # 检查文件格式
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'message': f'不支持的图片格式，仅支持: {", ".join(allowed_extensions)}'}), 400

    try:
        # 保存上传的图片
        upload_dir = os.path.join(DATA_DIR, 'uploads', 'bugs')
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}_{image.filename}"
        image_path = os.path.join(upload_dir, unique_filename)
        image.save(image_path)

        # 使用AI识别
        recognizer = get_recognizer()
        result = recognizer.recognize_screenshot(image_path)

        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'title': result.get('title', ''),
                    'severity': result.get('severity', '一般'),
                    'steps': result.get('steps', ''),
                    'expected_result': result.get('expected_result', ''),
                    'actual_result': result.get('actual_result', ''),
                    'screenshot_path': f'/uploads/bugs/{unique_filename}',
                    'recognized_at': result.get('recognized_at', ''),
                    'raw_text': result.get('raw_text', '')[:500] if result.get('raw_text') else ''
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'title': result.get('title', '未能自动识别'),
                    'severity': '一般',
                    'steps': '',
                    'expected_result': '',
                    'actual_result': '',
                    'screenshot_path': f'/uploads/bugs/{unique_filename}',
                    'recognized_at': result.get('recognized_at', ''),
                    'raw_text': result.get('raw_text', '')[:500] if result.get('raw_text') else '',
                    'warning': result.get('error', '识别过程中出现一些问题')
                }
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'识别失败: {str(e)}'}), 500


@app.route('/api/bug/list', methods=['GET'])
def list_bugs():
    """获取Bug列表（支持分页）"""
    from backend.bug_screenshot_recognizer import get_storage

    try:
        storage_path = os.path.join(DATA_DIR, 'bugs_recognized.json')
        storage = get_storage(storage_path)
        data = storage.load()

        bugs = data.get('bugs', [])

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        total = len(bugs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = bugs[start:end]

        return jsonify({
            'success': True,
            'data': paginated,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug/save', methods=['POST'])
def save_bug():
    """保存识别的bug到存储"""
    from backend.bug_screenshot_recognizer import get_storage

    data = request.json
    if not data:
        return jsonify({'success': False, 'message': '请提供bug数据'}), 400

    # 验证必要字段
    required_fields = ['title', 'severity', 'steps']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

    try:
        storage_path = os.path.join(DATA_DIR, 'bugs_recognized.json')
        storage = get_storage(storage_path)

        bug_info = {
            'title': data.get('title', ''),
            'severity': data.get('severity', '一般'),
            'steps': data.get('steps', ''),
            'expected_result': data.get('expected_result', ''),
            'actual_result': data.get('actual_result', ''),
            'screenshot_path': data.get('screenshot_path', ''),
            'recognized_at': data.get('recognized_at', datetime.now().isoformat())
        }

        if storage.add_bug(bug_info):
            return jsonify({'success': True, 'message': 'Bug记录已保存'})
        else:
            return jsonify({'success': False, 'message': '保存失败'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug/delete/<bug_id>', methods=['DELETE'])
def delete_bug(bug_id):
    """删除指定的bug记录"""
    from backend.bug_screenshot_recognizer import get_storage

    try:
        storage_path = os.path.join(DATA_DIR, 'bugs_recognized.json')
        storage = get_storage(storage_path)

        if storage.delete_bug(bug_id):
            return jsonify({'success': True, 'message': 'Bug记录已删除'})
        else:
            return jsonify({'success': False, 'message': 'Bug记录不存在或删除失败'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/bug/detail/<bug_id>', methods=['GET'])
def get_bug_detail(bug_id):
    """获取指定bug的详情"""
    from backend.bug_screenshot_recognizer import get_storage

    try:
        storage_path = os.path.join(DATA_DIR, 'bugs_recognized.json')
        storage = get_storage(storage_path)
        bug = storage.get_bug(bug_id)

        if bug:
            return jsonify({'success': True, 'data': bug})
        else:
            return jsonify({'success': False, 'message': 'Bug记录不存在'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== AI测试用例生成 API ====================

@app.route('/api/ai/generate-testcases', methods=['POST'])
def generate_testcases_ai():
    """从需求文档AI生成测试用例"""
    from backend.testcase_generator import TestCaseGenerator

    try:
        # 获取请求数据
        data = request.json or {}

        provider = data.get('provider', 'minimax')  # 默认使用minimax
        api_key = data.get('api_key')  # 可选的API Key
        group_id = data.get('group_id')  # MiniMax Group ID
        project_context = data.get('project_context', '')
        requirement_text = data.get('requirement_text', '')
        use_local = data.get('use_local', False)

        if not requirement_text:
            return jsonify({
                'success': False,
                'message': '请提供需求文档内容'
            }), 400

        # 创建生成器
        generator = TestCaseGenerator(provider=provider)

        # 设置API密钥（如果提供）
        print(f"[DEBUG] provider={provider}, api_key={'已提供' if api_key else 'None'}, group_id={'已提供' if group_id else 'None'}")
        if provider == 'minimax':
            from backend.minimax_client import get_minimax_client
            llm_client = get_minimax_client(api_key=api_key, group_id=group_id, local=use_local)
            generator.set_client(llm_client)
        elif provider == 'glm':
            from backend.glm_client import get_glm_client
            llm_client = get_glm_client(api_key=api_key, local=use_local)
            generator.set_client(llm_client)

        # 生成测试用例
        save_path = os.path.join(DATA_DIR, 'testcases.json')
        print(f"[DEBUG] 开始生成测试用例, requirement_text长度: {len(requirement_text)}")
        success, result = generator.generate_from_text(
            requirement_text,
            project_context,
            save_to=save_path
        )
        print(f"[DEBUG] 生成完成, success={success}, result={result}")

        if success:
            return jsonify({
                'success': True,
                'data': {
                    'total': result.get('total', 0),
                    'test_cases': result.get('test_cases', []),
                    'requirements_count': result.get('requirements_count', 0),
                    'generated_at': result.get('generated_at', ''),
                    'provider': result.get('provider', provider),
                    'errors': result.get('errors')  # 返回错误信息以便调试
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        }), 500


@app.route('/api/ai/generate-testcases-from-file', methods=['POST'])
def generate_testcases_from_file():
    """从上传的需求文档文件AI生成测试用例"""
    import traceback
    print(f"[DEBUG FILE] 收到请求")
    try:
        from backend.testcase_generator import TestCaseGenerator
        print(f"[DEBUG FILE] 模块导入成功")

        # 获取请求数据
        data = request.form or {}
        provider = data.get('provider', 'minimax')
        api_key = data.get('api_key')
        group_id = data.get('group_id')
        project_context = data.get('project_context', '')
        use_local = data.get('use_local', 'false').lower() == 'true'

        print(f"[DEBUG FILE] provider={provider}, api_key={'已提供' if api_key else 'None'}, group_id={'已提供' if group_id else 'None'}")

        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '请选择文件上传'
            }), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({
                'success': False,
                'message': '请选择文件'
            }), 400

        # 检查文件格式
        allowed_extensions = {'.docx', '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': f'不支持的文件格式，仅支持: {", ".join(allowed_extensions)}'
            }), 400

        # 保存上传的文件
        upload_dir = os.path.join(DATA_DIR, 'uploads', 'requirements')
        os.makedirs(upload_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 创建生成器
        generator = TestCaseGenerator(provider=provider)

        # 设置API密钥（如果提供）
        print(f"[DEBUG] provider={provider}, api_key={'已提供' if api_key else 'None'}, group_id={'已提供' if group_id else 'None'}")
        if provider == 'minimax':
            from backend.minimax_client import get_minimax_client
            llm_client = get_minimax_client(api_key=api_key, group_id=group_id, local=use_local)
            generator.set_client(llm_client)
        elif provider == 'glm':
            from backend.glm_client import get_glm_client
            llm_client = get_glm_client(api_key=api_key, local=use_local)
            generator.set_client(llm_client)

        # 生成测试用例
        save_path = os.path.join(DATA_DIR, 'testcases.json')
        print(f"[DEBUG FILE] 开始生成测试用例, file_path={file_path}")
        success, result = generator.generate_from_file(
            file_path,
            project_context,
            save_to=save_path
        )
        print(f"[DEBUG FILE] 生成完成, success={success}, result type={type(result)}, keys={result.keys() if isinstance(result, dict) else 'N/A'}")

        if success:
            test_cases = result.get('test_cases', [])
            print(f"[DEBUG FILE] 返回数据: total={result.get('total', 0)}, test_cases数量={len(test_cases)}")
            return jsonify({
                'success': True,
                'data': {
                    'total': result.get('total', 0),
                    'test_cases': test_cases,
                    'requirements_count': result.get('requirements_count', 0),
                    'source_file': result.get('source_file', ''),
                    'generated_at': result.get('generated_at', ''),
                    'provider': result.get('provider', provider),
                    'errors': result.get('errors')  # 返回错误信息以便调试
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 500

    except Exception as e:
        import traceback
        error_msg = f'生成失败: {str(e)}\n\n详情:\n{traceback.format_exc()}'
        print(f"[DEBUG FILE] 异常: {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500


@app.route('/api/ai/analyze-requirement', methods=['POST'])
def analyze_requirement():
    """分析需求文档，提取关键信息"""
    try:
        data = request.json or {}
        provider = data.get('provider', 'minimax')
        api_key = data.get('api_key')
        group_id = data.get('group_id')
        requirement_text = data.get('requirement_text', '')
        use_local = data.get('use_local', False)

        if not requirement_text:
            return jsonify({
                'success': False,
                'message': '请提供需求文档内容'
            }), 400

        # 根据provider创建客户端
        if provider == 'minimax':
            from backend.minimax_client import get_minimax_client
            client = get_minimax_client(api_key=api_key, group_id=group_id, local=use_local)
        else:
            from backend.glm_client import get_glm_client
            client = get_glm_client(api_key=api_key, local=use_local)

        # 分析需求
        success, result = client.analyze_requirement(requirement_text)

        if success:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}'
        }), 500


@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """获取AI配置信息"""
    # 从文件读取配置
    llm_config = load_json(os.path.join(DATA_DIR, 'llm_config.json'))
    if not isinstance(llm_config, dict):
        llm_config = {}

    glm_api_key = llm_config.get('glm_api_key', '') or os.getenv('GLM_API_KEY', '')
    minimax_api_key = llm_config.get('minimax_api_key', '') or os.getenv('MINIMAX_API_KEY', '')
    minimax_group_id = llm_config.get('minimax_group_id', '') or os.getenv('MINIMAX_GROUP_ID', '')

    return jsonify({
        'success': True,
        'data': {
            'providers': {
                'minimax': {
                    'name': 'MiniMax',
                    'has_api_key': bool(minimax_api_key),
                    'default_model': 'MiniMax-Text-01'
                },
                'glm': {
                    'name': '智谱 GLM-4',
                    'has_api_key': bool(glm_api_key),
                    'default_model': 'glm-4'
                }
            },
            'default_provider': llm_config.get('default_provider', 'minimax'),
            'supported_formats': ['.docx', '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif'],
            'saved_config': {
                'minimax_api_key': minimax_api_key,
                'minimax_group_id': minimax_group_id,
                'glm_api_key': glm_api_key,
                'default_provider': llm_config.get('default_provider', 'minimax')
            }
        }
    })


@app.route('/api/ai/config', methods=['POST'])
def set_ai_config():
    """设置AI配置"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': '请提供配置数据'}), 400

    # 构建配置
    llm_config = {
        'minimax_api_key': data.get('minimax_api_key', ''),
        'minimax_group_id': data.get('minimax_group_id', ''),
        'glm_api_key': data.get('glm_api_key', ''),
        'default_provider': data.get('default_provider', 'minimax'),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 保存到文件
    save_json(os.path.join(DATA_DIR, 'llm_config.json'), llm_config)

    # 同时更新环境变量
    if llm_config['minimax_api_key']:
        os.environ['MINIMAX_API_KEY'] = llm_config['minimax_api_key']
    if llm_config['minimax_group_id']:
        os.environ['MINIMAX_GROUP_ID'] = llm_config['minimax_group_id']
    if llm_config['glm_api_key']:
        os.environ['GLM_API_KEY'] = llm_config['glm_api_key']

    return jsonify({'success': True, 'message': '配置已保存'})


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '测试管理系统运行正常',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    import os
    # Railway 使用环境变量 PORT，本地开发使用 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    print("=" * 50)
    print("测试管理系统 - 后端服务启动中...")
    print("=" * 50)
    print(f"访问地址: http://localhost:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=debug)
