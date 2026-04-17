"""
缺陷分析模块 - 分析导入的Bug数据，生成统计数据
"""
import pandas as pd
import os
from datetime import datetime


class DefectAnalyzer:
    """缺陷分析器"""

    def __init__(self):
        self.df = None
        self.file_path = None

    def load_excel(self, file_path):
        """加载Excel文件"""
        self.file_path = file_path
        self.df = pd.read_excel(file_path)
        return len(self.df)

    def get_summary(self):
        """获取总体统计信息"""
        if self.df is None:
            return {}

        total = len(self.df)

        # 按缺陷分类统计（过滤掉NaN值）
        if '缺陷分类' in self.df.columns:
            by_category = self.df['缺陷分类'].dropna().value_counts().to_dict()
        else:
            by_category = {}

        # 按严重程度统计（过滤掉NaN值）
        if '严重程度' in self.df.columns:
            by_severity = self.df['严重程度'].dropna().value_counts().to_dict()
        else:
            by_severity = {}

        # 按处理人统计（过滤掉NaN值）
        if '处理人' in self.df.columns:
            by_handler = self.df['处理人'].dropna().value_counts().to_dict()
        else:
            by_handler = {}

        # 按验证人统计（过滤掉NaN值）
        if '验证人' in self.df.columns:
            by_verifier = self.df['验证人'].dropna().value_counts().to_dict()
        else:
            by_verifier = {}

        # 获取所有处理人（开发人员）
        handlers = []
        if '处理人' in self.df.columns:
            for handler in self.df['处理人'].dropna().unique():
                handlers.append(str(handler))

        # 获取所有验证人（测试人员）
        verifiers = []
        if '验证人' in self.df.columns:
            for verifier in self.df['验证人'].dropna().unique():
                verifiers.append(str(verifier))

        # 按状态统计（过滤掉NaN值）
        if '状态' in self.df.columns:
            by_status = self.df['状态'].dropna().value_counts().to_dict()
        else:
            by_status = {}

        # 按优先级统计（过滤掉NaN值）
        if '优先级' in self.df.columns:
            by_priority = self.df['优先级'].dropna().value_counts().to_dict()
        else:
            by_priority = {}

        # 按缺陷原因分类统计（过滤掉NaN值）
        if '缺陷原因分类' in self.df.columns:
            by_reason = self.df['缺陷原因分类'].dropna().value_counts().to_dict()
        else:
            by_reason = {}

        # 获取测试时间范围（使用最早和最晚的关闭时间）
        test_start = None
        test_end = None
        if '关闭时间' in self.df.columns:
            dates = self.df['关闭时间'].dropna()
            if len(dates) > 0:
                test_start = dates.min()
                test_end = dates.max()
        # 如果没有关闭时间，使用创建时间
        if not test_start and '创建时间' in self.df.columns:
            dates = self.df['创建时间'].dropna()
            if len(dates) > 0:
                test_start = dates.min()
                test_end = dates.max()
        # 如果没有创建时间，使用计划开始时间
        if not test_start and '计划开始时间' in self.df.columns:
            dates = self.df['计划开始时间'].dropna()
            if len(dates) > 0:
                test_start = dates.min()
                test_end = dates.max()

        # 获取版本号（项目名称）
        version = None
        if '版本' in self.df.columns:
            versions = self.df['版本'].dropna().unique()
            if len(versions) > 0:
                version = str(versions[0])

        # 获取处理人详情
        handlers = []
        if '处理人' in self.df.columns:
            for handler in self.df['处理人'].unique():
                if pd.notna(handler):
                    count = len(self.df[self.df['处理人'] == handler])
                    handler_df = self.df[self.df['处理人'] == handler]
                    # 获取该处理人的具体缺陷标题（过滤NaN）
                    titles = []
                    if '标题' in handler_df.columns:
                        for t in handler_df['标题'].tolist():
                            if pd.notna(t):
                                titles.append(str(t))
                    handlers.append({
                        'name': str(handler),
                        'count': count,
                        'titles': titles[:10]  # 最多10条
                    })

        # 获取简单的处理人名称列表（用于团队自动生成）
        handlers_list = []
        if '处理人' in self.df.columns:
            for handler in self.df['处理人'].dropna().unique():
                handlers_list.append(str(handler))

        # 获取所有缺陷标题
        all_titles = []
        if '标题' in self.df.columns:
            for _, row in self.df.iterrows():
                # 将NaN值转换为空字符串
                def safe_get(key, default=''):
                    val = row.get(key, default)
                    if pd.notna(val):
                        return str(val)
                    return ''

                all_titles.append({
                    'id': safe_get('编号'),
                    'title': safe_get('标题'),
                    'category': safe_get('缺陷分类'),
                    'severity': safe_get('严重程度'),
                    'handler': safe_get('处理人'),
                    'verifier': safe_get('验证人'),
                    'status': safe_get('状态'),
                    'reason': safe_get('缺陷具体原因'),
                    'reason_category': safe_get('缺陷原因分类'),
                    'create_time': safe_get('创建时间'),
                    'close_time': safe_get('关闭时间')
                })

        return {
            'total': total,
            'by_category': by_category,
            'by_severity': by_severity,
            'by_handler': by_handler,
            'by_verifier': by_verifier,
            'by_status': by_status,
            'by_priority': by_priority,
            'by_reason': by_reason,
            'test_start': test_start,
            'test_end': test_end,
            'version': version,
            'handlers': handlers,
            'handlers_list': handlers_list,
            'verifiers': verifiers,
            'all_titles': all_titles
        }

    def get_defect_list(self):
        """获取完整缺陷列表"""
        if self.df is None:
            return []

        result = []
        for _, row in self.df.iterrows():
            # 将NaN值转换为空字符串
            def safe_get(key, default=''):
                val = row.get(key, default)
                if pd.notna(val):
                    return str(val)
                return ''

            result.append({
                'id': safe_get('编号'),
                'title': safe_get('标题'),
                'module': safe_get('所属模块'),
                'category': safe_get('缺陷分类'),
                'reason': safe_get('缺陷具体原因'),
                'reason_category': safe_get('缺陷原因分类'),
                'severity': safe_get('严重程度'),
                'priority': safe_get('优先级'),
                'status': safe_get('状态'),
                'handler': safe_get('处理人'),
                'verifier': safe_get('验证人'),
                'create_time': safe_get('创建时间'),
                'close_time': safe_get('关闭时间')
            })
        return result


if __name__ == '__main__':
    # 测试
    analyzer = DefectAnalyzer()
    analyzer.load_excel(r'E:\June_workspace\oms\test_manager\缺陷信息(1).xlsx')
    summary = analyzer.get_summary()
    print(f"总缺陷数: {summary['total']}")
    print(f"按分类: {summary['by_category']}")
    print(f"按严重程度: {summary['by_severity']}")
    print(f"按处理人: {summary['by_handler']}")
