"""
测试报告生成模块
功能：生成测试报告（HTML、JSON、Excel格式）
"""
import os
import json
import uuid
import datetime
from typing import List, Dict


class ReportGenerator:
    """测试报告生成器"""

    def __init__(self, reports_dir):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate(self, result_ids: List[str] = None) -> Dict:
        """
        生成测试报告

        Args:
            result_ids: 测试结果ID列表，None表示所有结果

        Returns:
            生成的报告对象
        """
        # 加载测试结果
        results = self._load_results()

        if result_ids:
            results = [r for r in results if r.get('id') in result_ids]

        # 计算统计信息
        stats = self._calculate_stats(results)

        # 生成报告
        report = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_cases': stats['total'],
            'passed': stats['passed'],
            'failed': stats['failed'],
            'skipped': stats['skipped'],
            'pass_rate': stats['pass_rate'],
            'total_duration': stats['total_duration'],
            'results': results
        }

        # 保存报告
        self._save_report(report)

        return report

    def _load_results(self) -> List[Dict]:
        """加载测试结果"""
        data_dir = os.path.join(os.path.dirname(self.reports_dir), 'data')
        results_file = os.path.join(data_dir, 'test_results.json')

        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _calculate_stats(self, results: List[Dict]) -> Dict:
        """计算统计数据"""
        total = len(results)
        passed = sum(1 for r in results if r.get('status') == 'passed')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        skipped = sum(1 for r in results if r.get('status') == 'skipped')
        total_duration = sum(r.get('duration', 0) for r in results)

        pass_rate = round((passed / total * 100), 2) if total > 0 else 0

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': pass_rate,
            'total_duration': round(total_duration, 2)
        }

    def _save_report(self, report: Dict):
        """保存报告到文件"""
        filepath = os.path.join(self.reports_dir, f"{report['id']}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def generate_html_report(self, report: Dict) -> str:
        """
        生成HTML格式报告

        Args:
            report: 报告对象

        Returns:
            HTML字符串
        """
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {report.get('created_at', '')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #eee;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.total {{ background: #e3f2fd; }}
        .stat-card.passed {{ background: #e8f5e9; }}
        .stat-card.failed {{ background: #ffebee; }}
        .stat-card.skipped {{ background: #fff3e0; }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .passed .stat-value {{ color: #4caf50; }}
        .failed .stat-value {{ color: #f44336; }}
        .skipped .stat-value {{ color: #ff9800; }}
        .total .stat-value {{ color: #2196f3; }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .results-table th, .results-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .results-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        .results-table tr:hover {{
            background: #f8f9fa;
        }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .status.passed {{ background: #e8f5e9; color: #4caf50; }}
        .status.failed {{ background: #ffebee; color: #f44336; }}
        .status.skipped {{ background: #fff3e0; color: #ff9800; }}
        .status.pending {{ background: #e3f2fd; color: #2196f3; }}

        .error-message {{
            color: #f44336;
            font-size: 12px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试执行报告</h1>
        <p>生成时间: {report.get('created_at', '')}</p>

        <div class="summary">
            <div class="stat-card total">
                <div class="stat-value">{report.get('total_cases', 0)}</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-value">{report.get('passed', 0)}</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value">{report.get('failed', 0)}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-value">{report.get('skipped', 0)}</div>
                <div class="stat-label">跳过</div>
            </div>
        </div>

        <div class="summary">
            <div class="stat-card total">
                <div class="stat-value">{report.get('pass_rate', 0)}%</div>
                <div class="stat-label">通过率</div>
            </div>
            <div class="stat-card total">
                <div class="stat-value">{report.get('total_duration', 0)}s</div>
                <div class="stat-label">总耗时</div>
            </div>
        </div>

        <h2>详细结果</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>测试用例</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
"""

        for result in report.get('results', []):
            status = result.get('status', 'pending')
            html += f"""
                <tr>
                    <td>{result.get('case_name', '')}</td>
                    <td>{result.get('case_type', '')}</td>
                    <td><span class="status {status}">{status.upper()}</span></td>
                    <td>{result.get('duration', 0)}s</td>
                    <td>{result.get('error', '-')}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html

    def export_html(self, report_id: str) -> str:
        """
        导出HTML报告

        Args:
            report_id: 报告ID

        Returns:
            HTML文件路径
        """
        filepath = os.path.join(self.reports_dir, f"{report_id}.json")

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)

            html = self.generate_html_report(report)
            html_path = os.path.join(self.reports_dir, f"{report_id}.html")

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)

            return html_path

        return None
