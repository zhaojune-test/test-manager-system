"""
测试用例生成服务 - 根据需求文档自动生成功能测试用例
支持多种大模型：GLM、Minimax等
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

from backend.document_parser import DocumentParser, RequirementAnalyzer
from backend.glm_client import GLMClient, get_glm_client
from backend.minimax_client import MiniMaxClient, get_minimax_client


# 支持的模型类型
LLM_PROVIDERS = {
    'glm': {
        'class': GLMClient,
        'get_instance': get_glm_client,
        'name': '智谱 GLM-4',
        'default_model': 'glm-4'
    },
    'minimax': {
        'class': MiniMaxClient,
        'get_instance': get_minimax_client,
        'name': 'MiniMax',
        'default_model': 'minimax-m2.7'
    }
}


class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(self, llm_client: Union[GLMClient, MiniMaxClient] = None, provider: str = 'minimax'):
        """
        初始化测试用例生成器

        Args:
            llm_client: 大模型客户端实例（如果不提供，后续需通过 set_client 方法设置）
            provider: LLM提供商，可选 'glm' 或 'minimax'
        """
        self.document_parser = DocumentParser()
        self.requirement_analyzer = RequirementAnalyzer()
        self.provider = provider
        self.llm_client = llm_client  # 可以是 None，后续通过 set_client 设置

    def set_client(self, llm_client):
        """设置大模型客户端"""
        self.llm_client = llm_client

    @staticmethod
    def get_supported_providers() -> Dict:
        """获取支持的LLM提供商"""
        return {
            provider: info['name']
            for provider, info in LLM_PROVIDERS.items()
        }

    def generate_from_file(
        self,
        file_path: str,
        project_context: str = "",
        save_to: str = None
    ) -> Tuple[bool, Dict]:
        """
        从文档文件生成测试用例

        Args:
            file_path: 文档文件路径
            project_context: 项目背景信息
            save_to: 保存路径，如果不提供则不保存

        Returns:
            (success, result_dict_or_error)
        """
        # 1. 解析文档
        success, content = self.document_parser.parse(file_path)
        if not success:
            return False, f"文档解析失败: {content}"

        # 2. 提取需求
        requirements = self.requirement_analyzer.extract_requirements(content)

        if not requirements:
            return False, "未能从文档中提取到有效需求"

        # 3. 为每个需求生成测试用例
        all_test_cases = []
        errors = []

        import time

        print(f"[TESTCASE_GEN] 开始生成测试用例，共 {len(requirements)} 个需求")

        for i, req in enumerate(requirements):
            req_title = req.get('title', '未知')[:30]
            print(f"[TESTCASE_GEN] 处理需求 {i+1}/{len(requirements)}: {req_title}...")

            # 每个请求之间添加短暂延迟，避免rate limit
            if i > 0:
                time.sleep(1)  # 减少到1秒延迟

            success, result = self._generate_for_requirement(
                req,
                project_context
            )

            if success:
                # 给每个测试用例添加需求标题
                for case in result:
                    case['requirement_title'] = req.get('title', '未知需求')
                all_test_cases.extend(result)
                print(f"[TESTCASE_GEN] 需求 {i+1} 完成，获得 {len(result)} 个测试用例")
            else:
                # 检查是否是rate limit错误，如果是则重试一次
                err_str = str(result)
                if 'rate' in err_str.lower() or '520' in err_str or '超限' in err_str:
                    print(f"[TESTCASE_GEN] 需求 {i+1} 遇到rate limit，重试...")
                    time.sleep(3)
                    success, result = self._generate_for_requirement(req, project_context)
                    if success:
                        for case in result:
                            case['requirement_title'] = req.get('title', '未知需求')
                        all_test_cases.extend(result)
                        print(f"[TESTCASE_GEN] 需求 {i+1} 重试成功")
                        continue
                errors.append(f"需求 '{req_title}' 生成失败: {result}")
                print(f"[TESTCASE_GEN] 需求 {i+1} 失败: {err_str[:100]}")

        print(f"[TESTCASE_GEN] 生成完成，共 {len(all_test_cases)} 个测试用例, {len(errors)} 个错误")

        # 4. 标准化测试用例格式
        standardized_cases = self._standardize_test_cases(all_test_cases)

        # 5. 构建结果
        result_data = {
            'total': len(standardized_cases),
            'test_cases': standardized_cases,
            'requirements_count': len(requirements),
            'errors': errors if errors else None,
            'source_file': os.path.basename(file_path),
            'generated_at': datetime.now().isoformat(),
            'provider': self.provider
        }

        # 6. 保存到文件
        if save_to:
            self._save_test_cases(standardized_cases, save_to)

        return True, result_data

    def generate_from_text(
        self,
        requirement_text: str,
        project_context: str = "",
        save_to: str = None
    ) -> Tuple[bool, Dict]:
        """
        从文本内容生成测试用例

        Args:
            requirement_text: 需求文档文本内容
            project_context: 项目背景信息
            save_to: 保存路径

        Returns:
            (success, result_dict_or_error)
        """
        # 1. 提取需求
        requirements = self.requirement_analyzer.extract_requirements(requirement_text)

        if not requirements:
            requirements = [{
                'title': '需求概述',
                'description': requirement_text,
                'acceptance_criteria': ''
            }]

        # 2. 为每个需求生成测试用例
        all_test_cases = []
        errors = []

        import time

        print(f"[TESTCASE_GEN] 开始生成测试用例，共 {len(requirements)} 个需求")

        for i, req in enumerate(requirements):
            req_title = req.get('title', '未知')[:30]
            print(f"[TESTCASE_GEN] 处理需求 {i+1}/{len(requirements)}: {req_title}...")

            # 每个请求之间添加短暂延迟，避免rate limit
            if i > 0:
                time.sleep(1)  # 减少到1秒延迟

            success, result = self._generate_for_requirement(
                req,
                project_context
            )

            if success:
                # 给每个测试用例添加需求标题
                for case in result:
                    case['requirement_title'] = req.get('title', '未知需求')
                all_test_cases.extend(result)
                print(f"[TESTCASE_GEN] 需求 {i+1} 完成，获得 {len(result)} 个测试用例")
            else:
                # 检查是否是rate limit错误，如果是则重试一次
                err_str = str(result)
                if 'rate' in err_str.lower() or '520' in err_str or '超限' in err_str:
                    print(f"[TESTCASE_GEN] 需求 {i+1} 遇到rate limit，重试...")
                    time.sleep(3)
                    success, result = self._generate_for_requirement(req, project_context)
                    if success:
                        for case in result:
                            case['requirement_title'] = req.get('title', '未知需求')
                        all_test_cases.extend(result)
                        print(f"[TESTCASE_GEN] 需求 {i+1} 重试成功")
                        continue
                errors.append(f"需求 '{req_title}' 生成失败: {result}")
                print(f"[TESTCASE_GEN] 需求 {i+1} 失败: {err_str[:100]}")

        print(f"[TESTCASE_GEN] 生成完成，共 {len(all_test_cases)} 个测试用例, {len(errors)} 个错误")

        # 3. 标准化测试用例格式
        standardized_cases = self._standardize_test_cases(all_test_cases)

        # 4. 构建结果
        result_data = {
            'total': len(standardized_cases),
            'test_cases': standardized_cases,
            'requirements_count': len(requirements),
            'errors': errors if errors else None,
            'generated_at': datetime.now().isoformat(),
            'provider': self.provider
        }

        # 5. 保存到文件
        if save_to:
            self._save_test_cases(standardized_cases, save_to)

        return True, result_data

    def _generate_for_requirement(
        self,
        requirement: Dict,
        project_context: str
    ) -> Tuple[bool, List[Dict]]:
        """
        为单个需求生成测试用例

        Args:
            requirement: 需求字典
            project_context: 项目背景

        Returns:
            (success, test_cases_list)
        """
        # 构建需求文本
        req_text = f"## 需求名称\n{requirement.get('title', '')}\n\n## 需求描述\n{requirement.get('description', '')}"

        if requirement.get('acceptance_criteria'):
            req_text += f"\n\n## 验收标准\n{requirement.get('acceptance_criteria', '')}"

        # 调用大模型生成测试用例
        return self.llm_client.generate_test_cases(req_text, project_context)

    def _standardize_test_cases(self, test_cases: List[Dict]) -> List[Dict]:
        """
        标准化测试用例格式，确保所有必要字段都存在
        将步骤从JSON数组格式转换为文本格式
        """
        standardized = []

        for i, case in enumerate(test_cases):
            # 处理步骤：将 [{"action": "...", "expected": "..."}] 转为文本格式
            steps = case.get('steps', [])
            if isinstance(steps, list):
                # 将步骤数组转为文本格式
                steps_text = ""
                for idx, step in enumerate(steps, 1):
                    if isinstance(step, dict):
                        action = step.get('action', '')
                        expected = step.get('expected', '')
                        steps_text += f"{idx}. {action}\n   预期：{expected}\n"
                    else:
                        steps_text += f"{idx}. {step}\n"
                steps = steps_text.strip() if steps_text else ''
            elif steps is None:
                steps = ''

            standardized_case = {
                'id': case.get('id', case.get('case_id', str(uuid.uuid4()))),
                'name': case.get('name', case.get('case_name', f'测试用例_{i+1}')),
                'type': case.get('type', 'functional'),
                'description': case.get('description', ''),
                'priority': case.get('priority', 'medium'),
                'steps': steps,
                'expected_result': case.get('expected_result', ''),
                'tags': case.get('tags', []),
                'requirement_title': case.get('requirement_title', ''),
                'status': 'pending',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            standardized.append(standardized_case)

        return standardized

    def _save_test_cases(self, test_cases: List[Dict], save_path: str):
        """保存测试用例到文件"""
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 如果文件已存在，读取并合并
            existing = []
            if os.path.exists(save_path):
                with open(save_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)

            # 合并（避免重复）
            existing_ids = {case['id'] for case in existing}
            for case in test_cases:
                if case['id'] not in existing_ids:
                    existing.append(case)

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存测试用例失败: {e}")


def create_generator(provider: str = 'minimax', **kwargs) -> TestCaseGenerator:
    """创建测试用例生成器的便捷函数"""
    if provider == 'glm':
        client = get_glm_client(**kwargs)
    elif provider == 'minimax':
        client = get_minimax_client(**kwargs)
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")

    return TestCaseGenerator(llm_client=client, provider=provider)


def generate_test_cases_from_document(
    file_path: str,
    provider: str = 'minimax',
    api_key: str = None,
    group_id: str = None,
    project_context: str = "",
    local: bool = False
) -> Tuple[bool, Dict]:
    """
    从文档生成测试用例的便捷函数

    Args:
        file_path: 文档路径
        provider: LLM提供商 ('glm' 或 'minimax')
        api_key: API密钥
        group_id: MiniMax Group ID
        project_context: 项目背景
        local: 是否使用本地部署

    Returns:
        (success, result)
    """
    generator = create_generator(
        provider=provider,
        api_key=api_key,
        group_id=group_id,
        local=local
    )

    # 确定保存路径
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    save_to = os.path.join(base_dir, 'testcases.json')

    return generator.generate_from_file(file_path, project_context, save_to)


def generate_test_cases_from_text(
    text: str,
    provider: str = 'minimax',
    api_key: str = None,
    group_id: str = None,
    project_context: str = "",
    local: bool = False
) -> Tuple[bool, Dict]:
    """
    从文本生成测试用例的便捷函数

    Args:
        text: 需求文本
        provider: LLM提供商 ('glm' 或 'minimax')
        api_key: API密钥
        group_id: MiniMax Group ID
        project_context: 项目背景
        local: 是否使用本地部署

    Returns:
        (success, result)
    """
    generator = create_generator(
        provider=provider,
        api_key=api_key,
        group_id=group_id,
        local=local
    )

    # 确定保存路径
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    save_to = os.path.join(base_dir, 'testcases.json')

    return generator.generate_from_text(text, project_context, save_to)
