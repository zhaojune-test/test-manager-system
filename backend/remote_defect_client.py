"""
Remote Defect API Client - Fetches defect data from remote EDSP API
"""
import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from html import unescape
import json as json_module


class RemoteDefectClient:
    """远程缺陷API客户端"""

    # 状态映射
    STATUS_MAP = {
        0: '待处理',
        1: '处理中',
        2: '已修复',
        3: '暂不修复',
        4: '已关闭',
        5: '再次打开'
    }

    # 严重程度映射
    SEVERITY_MAP = {
        1: '致命',
        2: '严重',
        3: '一般',
        4: '轻微'
    }

    # 缺陷类型映射
    DEFECT_TYPE_MAP = {
        '1': '功能错误',
        '2': 'UI问题',
        '3': '性能问题',
        '4': '需求变更',
        '5': '安全问题',
        '6': '其他'
    }

    def __init__(self, api_url: str = None, project_id: str = None, token: str = None):
        """
        初始化远程缺陷API客户端

        Args:
            api_url: API基础URL，默认从环境变量读取
            project_id: 项目ID，默认从环境变量读取
            token: 认证Token，默认从环境变量读取
        """
        self.api_url = api_url or os.getenv('EDSP_API_URL', 'https://edsp.cosmoplat.com')
        self.project_id = project_id or os.getenv('EDSP_PROJECT_ID', '2007642735088656025')
        self.token = token or os.getenv('EDSP_API_TOKEN', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.token and self.project_id)

    def fetch_defects(self, version: str = None, page: int = 1, size: int = 1000) -> Tuple[bool, Dict]:
        """
        获取缺陷列表

        Args:
            version: 版本ID或版本名称（可选）
            page: 页码
            size: 每页数量

        Returns:
            (success, data_or_error)
        """
        try:
            url = f"{self.api_url}/project/defect/list/page"
            payload = {
                "projectId": self.project_id,
                "page": page,
                "size": size
            }
            if version:
                payload["version"] = version

            # 尝试POST请求
            response = self.session.post(url, json=payload, timeout=30)

            # 如果返回405，尝试GET请求
            if response.status_code == 405:
                response = self.session.get(url, params=payload, timeout=30)

            response.raise_for_status()

            # 检查响应状态和内容
            response_text = response.text
            if not response_text:
                return False, "API返回空响应"

            try:
                result = json_module.loads(response_text)
            except json_module.JSONDecodeError as e:
                # 返回原始响应内容用于调试
                return False, f"API返回无效JSON (响应前100字符): {response_text[:100]}"

            if response.status_code == 200:
                return True, result
            else:
                return False, result.get('message', '请求失败')

        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到远程服务器"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "认证失败，请检查Token是否有效"
            elif e.response.status_code == 403:
                return False, "无访问权限，请检查Token权限"
            elif e.response.status_code == 405:
                return False, "HTTP方法不支持，请检查API端点"
            else:
                return False, f"HTTP错误: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def fetch_versions(self) -> Tuple[bool, List[Dict]]:
        """
        获取项目版本列表

        Returns:
            (success, versions_list)
        """
        try:
            # 使用与fetch_defects相同的API，版本列表在响应的versionList字段
            url = f"{self.api_url}/project/defect/list/page"
            payload = {
                "projectId": self.project_id,
                "page": 1,
                "size": 1
            }

            # 尝试POST请求
            response = self.session.post(url, json=payload, timeout=30)

            # 如果返回405，尝试GET请求
            if response.status_code == 405:
                response = self.session.get(url, params=payload, timeout=30)

            response.raise_for_status()

            # 检查响应状态和内容
            response_text = response.text
            if not response_text:
                return False, []

            try:
                result = json_module.loads(response_text)
            except json_module.JSONDecodeError:
                return False, []

            # 版本信息在pageResult的versionList中
            page_result = result.get('pageResult', {})
            versions = page_result.get('versionList', [])

            # 转换为 [{id, name}, ...] 格式
            version_list = []
            for v in versions:
                if isinstance(v, dict):
                    version_list.append({
                        'id': v.get('id', ''),
                        'name': v.get('versionName', v.get('name', ''))
                    })
                else:
                    version_list.append({'id': str(v), 'name': str(v)})

            return True, version_list

        except Exception as e:
            return False, []

    def parse_defects(self, api_response: Dict) -> List[Dict]:
        """
        解析API响应中的缺陷数据

        Args:
            api_response: API响应数据

        Returns:
            解析后的缺陷列表
        """
        defects = []

        # 从pageResult中获取缺陷列表
        page_result = api_response.get('pageResult', {})
        records = page_result.get('records', [])

        for record in records:
            defect = self._parse_single_defect(record)
            defects.append(defect)

        return defects

    def _parse_single_defect(self, record: Dict) -> Dict:
        """解析单条缺陷记录"""
        # 解析description HTML
        description = record.get('description', '')
        steps, expected, actual = self._parse_description_html(description)

        # 获取状态映射
        status_code = record.get('status', 0)
        status = self.STATUS_MAP.get(status_code, '未知')

        # 获取严重程度映射
        severity_code = record.get('severityDegree', 3)
        severity = self.SEVERITY_MAP.get(severity_code, '一般')

        # 获取缺陷类型映射
        defect_type_code = str(record.get('defectType', ''))
        category = self.DEFECT_TYPE_MAP.get(defect_type_code, '其他')

        return {
            'id': record.get('number', record.get('id', '')),
            'title': record.get('title', ''),
            'category': category,
            'severity': severity,
            'status': status,
            'handler': record.get('handleName', ''),
            'verifier': record.get('verifierName', ''),
            'create_time': record.get('createdAt', ''),
            'close_time': record.get('closeDate', ''),
            'steps': steps,
            'expected_result': expected,
            'actual_result': actual,
            'reason': steps,  # 缺陷原因用步骤代替
            'reason_category': category,
            'pm': record.get('rpName', ''),
            'version': record.get('versionName', record.get('version', '')),
            'project_name': record.get('projectName', '')
        }

    def _parse_description_html(self, html: str) -> Tuple[str, str, str]:
        """
        解析description HTML，提取操作步骤、预期结果、实际结果

        Args:
            html: HTML格式的description

        Returns:
            (steps, expected_result, actual_result)
        """
        steps = ''
        expected = ''
        actual = ''

        if not html:
            return steps, expected, actual

        # 移除HTML标签但保留文本
        def extract_section(html_text, section_name) -> str:
            """提取指定章节的内容"""
            # 匹配 [section_name] 后面的内容，直到下一个 [xxx] 或结束
            pattern = rf'\[{section_name}\]\s*</h2>\s*<p>(.*?)</p>'
            match = re.search(pattern, html_text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                # 处理图片标签，提取src
                img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
                img_matches = re.findall(img_pattern, content)
                if img_matches:
                    # 如果有图片，添加图片URL
                    img_urls = '\n'.join([f'[图片: {url}]' for url in img_matches])
                    content = re.sub(r'<img[^>]+>', '', content)
                    content = content.strip() + '\n' + img_urls
                # 清理其他HTML标签
                content = re.sub(r'<[^>]+>', '', content)
                # 解码HTML实体
                content = unescape(content)
                return content.strip()
            return ''

        steps = extract_section(html, '操作步骤')
        expected = extract_section(html, '预期结果')
        actual = extract_section(html, '实际结果')

        return steps, expected, actual

    def get_statistics(self, defects: List[Dict]) -> Dict:
        """
        计算缺陷统计信息

        Args:
            defects: 缺陷列表

        Returns:
            统计信息字典
        """
        total = len(defects)

        # 按严重程度统计
        by_severity = {}
        for d in defects:
            severity = d.get('severity', '未知')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # 按状态统计
        by_status = {}
        for d in defects:
            status = d.get('status', '未知')
            by_status[status] = by_status.get(status, 0) + 1

        # 按处理人统计
        by_handler = {}
        for d in defects:
            handler = d.get('handler', '')
            if handler:
                by_handler[handler] = by_handler.get(handler, 0) + 1

        # 按分类统计
        by_category = {}
        for d in defects:
            category = d.get('category', '未知')
            by_category[category] = by_category.get(category, 0) + 1

        return {
            'total': total,
            'by_severity': by_severity,
            'by_status': by_status,
            'by_handler': by_handler,
            'by_category': by_category
        }


class DefectCache:
    """缺陷数据缓存"""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'remote_defects_cache.json')
        self.cache_timeout = 3600  # 1小时

    def get(self, version: str) -> Optional[Dict]:
        """获取缓存数据"""
        try:
            if not os.path.exists(self.cache_file):
                return None

            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查版本是否匹配
            if cache_data.get('version') != version:
                return None

            # 检查是否过期
            cached_time = cache_data.get('cached_at', 0)
            if datetime.now().timestamp() - cached_time > self.cache_timeout:
                return None

            return cache_data.get('data')

        except Exception:
            return None

    def set(self, version: str, data: Dict):
        """设置缓存数据"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)

            cache_data = {
                'version': version,
                'cached_at': datetime.now().timestamp(),
                'data': data
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception:
            pass

    def clear(self):
        """清除缓存"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception:
            pass


# 全局实例
_client_instance = None
_cache_instance = None


def get_remote_client(api_url: str = None, project_id: str = None, token: str = None) -> RemoteDefectClient:
    """获取全局客户端实例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = RemoteDefectClient(api_url, project_id, token)
    return _client_instance


def get_cache(cache_dir: str) -> DefectCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DefectCache(cache_dir)
    return _cache_instance
