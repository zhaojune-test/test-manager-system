"""
Bug Screenshot Recognizer - Baidu AI Vision integration for bug screenshot analysis
"""
import os
import json
import uuid
import base64
from datetime import datetime
from typing import Dict, Optional

# Try to import Baidu AIP, fallback to basic OCR if not available
try:
    from aip import AipOcr, AipImageProcess
    BAIDU_SDK_AVAILABLE = True
except ImportError:
    BAIDU_SDK_AVAILABLE = False

# Try PIL for basic image handling
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try pytesseract for fallback OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class BugScreenshotRecognizer:
    """Bug截图识别器 - 使用百度AI识别截图中的bug信息"""

    # Bug严重程度关键词映射
    SEVERITY_KEYWORDS = {
        '严重': ['严重', '崩溃', '闪退', '致命', 'critical', 'crash', 'fatal'],
        '一般': ['一般', '普通', '错误', 'bug', 'major', 'error'],
        '轻微': ['轻微', '小', '提示', 'minor', 'warning', 'info'],
        '建议': ['建议', '优化', 'enhancement', 'suggest']
    }

    def __init__(self, app_id: str = None, api_key: str = None, secret_key: str = None):
        """
        初始化百度AI客户端

        Args:
            app_id: 百度应用ID (可选，从环境变量BAIDU_APP_ID读取)
            api_key: 百度API Key (可选，从环境变量BAIDU_API_KEY读取)
            secret_key: 百度Secret Key (可选，从环境变量BAIDU_SECRET_KEY读取)
        """
        self.app_id = app_id or os.getenv('BAIDU_APP_ID', '')
        self.api_key = api_key or os.getenv('BAIDU_API_KEY', '')
        self.secret_key = secret_key or os.getenv('BAIDU_SECRET_KEY', '')
        self.client = None

        if BAIDU_SDK_AVAILABLE and self.app_id and self.api_key and self.secret_key:
            try:
                self.client = AipOcr(self.app_id, self.api_key, self.secret_key)
            except Exception as e:
                print(f"Failed to initialize Baidu OCR client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        """检查是否已配置百度API"""
        return self.client is not None

    def recognize_screenshot(self, image_path: str) -> Dict:
        """
        识别截图中的bug信息

        Args:
            image_path: 图片文件路径

        Returns:
            包含识别结果的字典
        """
        result = {
            'title': '',
            'severity': '一般',
            'steps': '',
            'expected_result': '',
            'actual_result': '',
            'screenshot_path': image_path,
            'recognized_at': datetime.now().isoformat(),
            'raw_text': '',
            'success': False,
            'error': None
        }

        try:
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # 优先使用百度AI OCR
            if self.client:
                ocr_result = self._baidu_ocr(image_data)
                if ocr_result:
                    result['raw_text'] = ocr_result
                    self._parse_bug_info(result, ocr_result)
                    result['success'] = True
                    return result

            # 备用: 使用本地OCR
            if PIL_AVAILABLE and TESSERACT_AVAILABLE:
                local_ocr_result = self._local_ocr(image_path)
                if local_ocr_result:
                    result['raw_text'] = local_ocr_result
                    self._parse_bug_info(result, local_ocr_result)
                    result['success'] = True
                    return result

            # 如果都没有，尝试基础识别
            if PIL_AVAILABLE:
                basic_text = self._basic_image_analysis(image_path)
                result['raw_text'] = basic_text
                self._parse_bug_info(result, basic_text)
                result['success'] = True
                return result

            result['error'] = 'No OCR engine available'
            return result

        except Exception as e:
            result['error'] = str(e)
            return result

    def _baidu_ocr(self, image_data: bytes) -> Optional[str]:
        """使用百度OCR识别文字"""
        try:
            # 使用通用文字识别
            result = self.client.basicGeneral(image_data)

            if 'words_result' in result and result['words_result']:
                words = [item['words'] for item in result['words_result']]
                return '\n'.join(words)

            # 尝试高精度版
            result = self.client.basicAccurate(image_data)
            if 'words_result' in result and result['words_result']:
                words = [item['words'] for item in result['words_result']]
                return '\n'.join(words)

            return None
        except Exception as e:
            print(f"Baidu OCR failed: {e}")
            return None

    def _local_ocr(self, image_path: str) -> Optional[str]:
        """使用本地Tesseract OCR"""
        try:
            if PIL_AVAILABLE and TESSERACT_AVAILABLE:
                img = Image.open(image_path)
                # 使用中英文混合识别
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return text.strip()
            return None
        except Exception as e:
            print(f"Local OCR failed: {e}")
            return None

    def _basic_image_analysis(self, image_path: str) -> str:
        """基础图片分析（当没有OCR时）"""
        try:
            if PIL_AVAILABLE:
                img = Image.open(image_path)
                return f"[图片尺寸: {img.size[0]}x{img.size[1]}] 图片分析功能待完善，请配置百度OCR API"
            return "[无法分析图片]"
        except Exception as e:
            return f"[图片读取失败: {e}]"

    def _parse_bug_info(self, result: Dict, raw_text: str):
        """解析OCR识别出的文字，提取bug相关信息"""
        if not raw_text:
            result['title'] = '未能识别出文字'
            return

        lines = raw_text.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        # 尝试识别bug标题（通常是第一行或包含"bug"、"错误"、"问题"等关键词的行）
        title_candidates = []
        for i, line in enumerate(lines[:5]):  # 只检查前5行
            line_lower = line.lower()
            if any(kw in line_lower for kw in ['bug', '错误', '问题', '异常', '失败', 'error', 'issue']):
                title_candidates.append((i, line))

        if title_candidates:
            # 选择第一个作为标题
            result['title'] = title_candidates[0][1]
        elif lines:
            # 使用第一行作为标题
            result['title'] = lines[0][:100]  # 限制长度

        # 识别严重程度
        full_text = '\n'.join(lines)
        result['severity'] = self._detect_severity(full_text)

        # 提取操作步骤（查找包含数字序号的行）
        steps_lines = []
        for line in lines:
            # 匹配 "1." "1、" "步骤1" 等格式
            if any(pattern in line for pattern in ['1.', '2.', '3.', '1、', '2、', '3、', '步骤', 'step']):
                steps_lines.append(line)

        if steps_lines:
            result['steps'] = '\n'.join(steps_lines)

        # 尝试区分预期结果和实际结果
        expected_lines = []
        actual_lines = []
        in_expected = False
        in_actual = False

        for line in lines:
            line_lower = line.lower()
            if '预期' in line or '应该' in line or '期望' in line:
                in_expected = True
                in_actual = False
                continue
            if '实际' in line or '但是' in line or '却' in line:
                in_actual = True
                in_expected = False
                continue
            if in_expected:
                expected_lines.append(line)
            elif in_actual:
                actual_lines.append(line)

        if expected_lines:
            result['expected_result'] = '\n'.join(expected_lines)
        if actual_lines:
            result['actual_result'] = '\n'.join(actual_lines)

        # 如果步骤为空，使用剩余的有效行
        if not result['steps'] and len(lines) > 1:
            result['steps'] = '\n'.join(lines[1:6])  # 使用第2-6行作为步骤

    def _detect_severity(self, text: str) -> str:
        """检测bug严重程度"""
        text_lower = text.lower()

        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return severity

        return '一般'  # 默认严重程度


class BugRecordStorage:
    """Bug记录存储器"""

    def __init__(self, storage_path: str):
        """
        初始化存储器

        Args:
            storage_path: JSON文件路径
        """
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """确保存储文件存在"""
        if not os.path.exists(self.storage_path):
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({'bugs': [], 'total': 0, 'last_updated': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

    def load(self) -> Dict:
        """加载所有bug记录"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'bugs': [], 'total': 0}

    def save(self, data: Dict) -> bool:
        """保存bug记录"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save bug records: {e}")
            return False

    def add_bug(self, bug_info: Dict) -> bool:
        """添加一条bug记录"""
        try:
            data = self.load()

            # 生成唯一ID
            bug_info['id'] = str(uuid.uuid4())[:8]

            data['bugs'].insert(0, bug_info)  # 新记录插入到最前面
            data['total'] = len(data['bugs'])

            return self.save(data)
        except Exception as e:
            print(f"Failed to add bug: {e}")
            return False

    def delete_bug(self, bug_id: str) -> bool:
        """删除一条bug记录"""
        try:
            data = self.load()
            original_count = len(data['bugs'])
            data['bugs'] = [b for b in data['bugs'] if b.get('id') != bug_id]

            if len(data['bugs']) < original_count:
                data['total'] = len(data['bugs'])
                return self.save(data)

            return False  # 未找到要删除的记录
        except Exception as e:
            print(f"Failed to delete bug: {e}")
            return False

    def get_bug(self, bug_id: str) -> Optional[Dict]:
        """获取指定bug记录"""
        try:
            data = self.load()
            for bug in data['bugs']:
                if bug.get('id') == bug_id:
                    return bug
            return None
        except Exception:
            return None


# 全局实例
_recognizer_instance = None
_storage_instance = None


def get_recognizer() -> BugScreenshotRecognizer:
    """获取全局识别器实例"""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = BugScreenshotRecognizer()
    return _recognizer_instance


def get_storage(storage_path: str = None) -> BugRecordStorage:
    """获取全局存储器实例"""
    global _storage_instance
    if storage_path and _storage_instance is None:
        _storage_instance = BugRecordStorage(storage_path)
    return _storage_instance
