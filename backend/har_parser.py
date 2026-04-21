"""
HAR (HTTP Archive) 文件解析器
从浏览器开发者工具导出的 HAR 文件中提取 API 请求信息
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, parse_qs


class HarParser:
    """HAR 文件解析器"""

    # 常见的不需要测试的静态资源
    STATIC_EXTENSIONS = {
        '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.woff', '.woff2', '.ttf', '.eot', '.map', '.webp', '.webm',
        '.mp4', '.mp3', '.wav', '.ogg', '.flac', '.avi', '.mov',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.pdf', '.doc', '.docx',
        '.xls', '.xlsx', '.ppt', '.pptx', '.exe', '.dmg', '.pkg'
    }

    # 需要过滤的域名（前端静态资源）
    FILTER_DOMAINS = {
        'cdn', 'static', 'assets', 'images', 'img', 'fonts', 'media',
        'analytics', 'tracking', 'ads', 'partner', 'sentry', 'monitor',
        'metrics', 'logging', 'log', 'telemetry', 'opentelemetry'
    }

    # 主要/核心业务API关键词（这些优先保留）
    MAIN_API_KEYWORDS = {
        'login', 'signin', 'logout', 'signout', 'auth', 'token', 'account',
        'user', 'profile', 'password', 'register', 'signup',
        'project', 'data', 'list', 'detail', 'info', 'query',
        'create', 'add', 'update', 'edit', 'delete', 'remove',
        'submit', 'save', 'export', 'import', 'upload', 'download',
        'config', 'setting', 'permission', 'role', 'menu', 'nav',
        'dashboard', 'home', 'index', 'report', 'chart', 'graph',
        'analyze', 'analysis', 'score', 'health', 'risk', 'issue'
    }

    # 过滤的非核心API路径关键词
    FILTER_PATHS = {
        'health', 'ping', 'heartbeat', 'monitor', 'metrics', 'stats',
        'tracking', 'analytics', 'telemetry', 'log', 'logging',
        'favicon', 'robots.txt', 'sitemap', 'manifest',
        'browser', 'config', 'environment', 'version'
    }

    # 过滤的完整域名（非业务API）
    FILTER_DOMAINS_EXACT = {
        'umami.hdt.cosmoplat.com',  # 埋点/分析
        'sentry.io',  # 错误监控
        'cdn.jsdelivr.net',
        'cdn.bootcdn.net',
        'lib.baomitu.com',
        '公共的cdn等'
    }

    # 核心业务域名关键词（这些域名优先保留）
    CORE_DOMAIN_KEYWORDS = {
        'api', 'backend', 'server', 'service', 'edsp', 'erp', 'crm',
        'boss', 'workflow', 'bpm', 'oa'
    }

    def __init__(self):
        self.entries = []
        self.api_endpoints = []

    def parse_file(self, file_path: str) -> Tuple[bool, str]:
        """
        解析 HAR 文件

        Args:
            file_path: HAR 文件路径

        Returns:
            (success, result_or_error)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                har_data = json.load(f)
            return self.parse_content(har_data)
        except json.JSONDecodeError as e:
            return False, f"HAR 文件格式错误（非 JSON）: {str(e)}"
        except Exception as e:
            return False, f"解析 HAR 文件失败: {str(e)}"

    def parse_content(self, har_content: Dict) -> Tuple[bool, str]:
        """
        解析 HAR 内容字典

        Args:
            har_content: HAR JSON 内容

        Returns:
            (success, result_or_error)
        """
        try:
            # 验证 HAR 格式
            if 'log' not in har_content:
                return False, "无效的 HAR 格式：缺少 'log' 字段"

            log = har_content['log']

            # 验证必要字段
            if 'entries' not in log:
                return False, "无效的 HAR 格式：缺少 'entries' 字段"

            self.entries = log.get('entries', [])

            if not self.entries:
                return False, "HAR 文件中没有任何请求记录"

            # 提取 API 端点
            self.api_endpoints = self._extract_api_endpoints()

            if not self.api_endpoints:
                return False, "未从 HAR 文件中提取到任何 API 请求"

            return True, f"成功解析 {len(self.entries)} 条请求，提取到 {len(self.api_endpoints)} 个 API 端点"

        except Exception as e:
            return False, f"解析 HAR 内容失败: {str(e)}"

    def _extract_api_endpoints(self) -> List[Dict]:
        """从 HAR 条目中提取 API 端点"""
        endpoints = []
        seen_urls = set()  # 用于去重

        for entry in self.entries:
            try:
                request = entry.get('request', {})
                if not request:
                    continue

                # 获取基本信息
                url = request.get('url', '')
                method = request.get('method', 'GET').upper()
                headers = self._normalize_headers(request.get('headers', []))

                # 解析 URL
                parsed = urlparse(url)
                path = parsed.path
                domain = parsed.netloc
                domain_lower = domain.lower()

                # 过滤非正常请求
                # 1. 过滤 OPTIONS 请求（CORS预检请求）
                if method == 'OPTIONS':
                    continue

                # 2. 过滤静态资源
                if self._is_static_resource(url, path):
                    continue

                # 3. 过滤非 API 请求
                if not self._is_api_request(path, domain):
                    continue

                # 4. 过滤非核心域名（如埋点、监控等）
                if self._is_non_core_domain(domain_lower):
                    continue

                # 5. 过滤非核心业务API（只有当不是核心域名时才过滤）
                if not self._is_main_api(path, method):
                    # 如果域名不明确是核心业务系统，则跳过
                    if not self._has_core_domain_keyword(domain_lower):
                        continue

                # 解析查询参数
                query_params = {}
                for param in request.get('queryString', []):
                    query_params[param.get('name', '')] = param.get('value', '')

                # 解析请求体
                post_data = request.get('postData', {})
                body = None
                if post_data:
                    mime_type = post_data.get('mimeType', '')
                    if 'application/json' in mime_type:
                        try:
                            body = json.loads(post_data.get('text', '{}'))
                        except:
                            body = post_data.get('text')
                    else:
                        body = post_data.get('text')

                # 获取响应信息
                response = entry.get('response', {})
                status = response.get('status', 0)
                response_headers = self._normalize_headers(response.get('headers', []))

                # 构建唯一标识（用于去重）
                unique_key = f"{method}:{path}"
                if unique_key in seen_urls:
                    continue
                seen_urls.add(unique_key)

                # 构建 API 端点信息
                is_main = self._is_main_api(path, method) or self._has_core_domain_keyword(domain_lower)
                endpoint = {
                    'id': str(uuid.uuid4()),
                    'name': self._generate_name(method, path),
                    'description': f'{method} {path}',
                    'type': 'api',
                    'method': method,
                    'url': self._build_test_url(parsed, query_params),
                    'domain': domain,
                    'path': path,
                    'headers': headers,
                    'params': query_params,
                    'body': body,
                    'response_status': status,
                    'response_headers': response_headers,
                    'is_main': is_main,
                    'priority': self._determine_priority(method, status, path),
                    'status': 'pending',
                    'test_data': {
                        'url': self._build_test_url(parsed, query_params),
                        'method': method,
                        'headers': headers,
                        'params': query_params,
                        'body': body
                    },
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                endpoints.append(endpoint)

            except Exception as e:
                # 跳过无效条目
                continue

        return endpoints

    def _is_non_core_domain(self, domain: str) -> bool:
        """判断是否为非核心域名"""
        # 直接过滤的域名
        if domain in self.FILTER_DOMAINS_EXACT:
            return True

        # 过滤 umami 等埋点域名
        if 'umami' in domain or 'telemetry' in domain or 'tracking' in domain:
            return True

        # 过滤 sentry 等监控域名
        if 'sentry' in domain or 'monitor' in domain:
            return True

        return False

    def _has_core_domain_keyword(self, domain: str) -> bool:
        """判断域名是否包含核心业务关键词"""
        for keyword in self.CORE_DOMAIN_KEYWORDS:
            if keyword in domain:
                return True
        return False

    def _is_static_resource(self, url: str, path: str) -> bool:
        """判断是否为静态资源"""
        # 检查文件扩展名
        lower_url = url.lower()
        for ext in self.STATIC_EXTENSIONS:
            if lower_url.endswith(ext) or f'.{ext}?' in lower_url:
                return True

        # 检查路径
        path_lower = path.lower()
        for keyword in ['/static/', '/assets/', '/public/', '/dist/', '/build/']:
            if keyword in path_lower:
                return True

        return False

    def _is_api_request(self, path: str, domain: str) -> bool:
        """判断是否为 API 请求"""
        path_lower = path.lower()
        domain_lower = domain.lower()

        # 首先过滤明显的非API请求
        for keyword in self.FILTER_PATHS:
            if keyword in path_lower:
                return False

        # 检查域名是否是需要过滤的域名
        for keyword in self.FILTER_DOMAINS:
            if keyword in domain_lower:
                # 检查是否是主要业务API
                if any(kw in path_lower for kw in self.MAIN_API_KEYWORDS):
                    return True
                return False

        # 检查路径是否像 API
        api_indicators = ['/api/', '/rest/', '/v1/', '/v2/', '/v3/', '/graphql',
                          '/rpc/', '/jsonrpc', '/query/', '/mutation/']
        for indicator in api_indicators:
            if indicator in path_lower:
                return True

        # 如果路径包含主要业务关键词，也认为是API
        if any(kw in path_lower for kw in self.MAIN_API_KEYWORDS):
            return True

        return False

    def _is_main_api(self, path: str, method: str) -> bool:
        """判断是否为主要/核心业务API"""
        path_lower = path.lower()

        # 核心业务API判断
        core_keywords = [
            'login', 'signin', 'logout', 'auth', 'token',
            'project', 'user', 'profile', 'account',
            'data', 'list', 'detail', 'info', 'query',
            'create', 'add', 'update', 'edit', 'delete',
            'submit', 'save', 'export', 'import',
            'config', 'setting', 'permission', 'role', 'menu',
            'dashboard', 'report', 'chart', 'analyze', 'health'
        ]

        for keyword in core_keywords:
            if keyword in path_lower:
                return True

        # POST/PUT/DELETE 的数据操作API通常是核心API
        if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if '/api/' in path_lower or '/rest/' in path_lower:
                return True

        return False

    def _normalize_headers(self, headers: List[Dict]) -> Dict[str, str]:
        """规范化请求头为字典格式"""
        result = {}
        for header in headers:
            name = header.get('name', '')
            value = header.get('value', '')
            if name and value:
                # 跳过一些不需要测试的头部
                lower_name = name.lower()
                if lower_name not in ['host', 'content-length', 'connection',
                                      'accept-encoding', 'user-agent', 'sec-ch-ua',
                                      'sec-ch-ua-mobile', 'sec-ch-ua-platform']:
                    result[name] = value
        return result

    def _generate_name(self, method: str, path: str) -> str:
        """生成测试用例名称"""
        # 从路径中提取有意义的名称
        parts = [p for p in path.split('/') if p]
        if len(parts) >= 2:
            # 使用最后两个路径部分
            name = '_'.join(parts[-2:]).replace('-', '_').replace('.', '_')
        elif parts:
            name = parts[-1].replace('-', '_').replace('.', '_')
        else:
            name = 'root'

        # 添加方法前缀
        return f"{method}_{name}"

    def _build_test_url(self, parsed: urlparse, query_params: Dict) -> str:
        """构建测试 URL"""
        # 使用域名作为测试基础
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if query_params:
            # 保留部分关键参数，用占位符替换敏感参数
            test_params = {}
            sensitive_keywords = ['token', 'key', 'secret', 'password', 'sign',
                                  'timestamp', 'nonce', 'signature', 'session']

            for k, v in query_params.items():
                lower_k = k.lower()
                if any(s in lower_k for s in sensitive_keywords):
                    test_params[k] = f"{{{{{k}}}}}"
                else:
                    test_params[k] = v

            # 构建新的查询字符串
            from urllib.parse import urlencode
            query_string = urlencode(test_params)
            base_url = f"{base_url}?{query_string}"

        return base_url

    def _determine_priority(self, method: str, status: int, path: str = '') -> str:
        """确定测试优先级"""
        # 如果是核心业务API，优先HIGH
        if path and self._is_main_api(path, method):
            return 'high'

        # POST/PUT/DELETE 请求更高优先级
        if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if status >= 400:
                return 'high'
            return 'medium'

        # GET 请求默认 medium
        if status >= 400:
            return 'high'
        return 'medium'

    def get_api_endpoints(self) -> List[Dict]:
        """获取提取的 API 端点列表"""
        return self.api_endpoints

    def get_summary(self) -> Dict:
        """获取解析摘要"""
        methods = {}
        domains = {}

        for endpoint in self.api_endpoints:
            # 统计方法
            method = endpoint.get('method', 'GET')
            methods[method] = methods.get(method, 0) + 1

            # 统计域名
            domain = endpoint.get('domain', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1

        return {
            'total': len(self.api_endpoints),
            'by_method': methods,
            'by_domain': domains,
            'total_requests': len(self.entries)
        }


def parse_har_file(file_path: str) -> Tuple[bool, Dict]:
    """
    解析 HAR 文件的便捷函数

    Args:
        file_path: HAR 文件路径

    Returns:
        (success, result_dict_or_error)
    """
    parser = HarParser()
    success, message = parser.parse_file(file_path)

    if not success:
        return False, message

    return True, {
        'endpoints': parser.get_api_endpoints(),
        'summary': parser.get_summary()
    }


def parse_har_content(har_content: Dict) -> Tuple[bool, Dict]:
    """
    解析 HAR 内容的便捷函数

    Args:
        har_content: HAR JSON 内容字典

    Returns:
        (success, result_dict_or_error)
    """
    parser = HarParser()
    success, message = parser.parse_content(har_content)

    if not success:
        return False, message

    return True, {
        'endpoints': parser.get_api_endpoints(),
        'summary': parser.get_summary()
    }
