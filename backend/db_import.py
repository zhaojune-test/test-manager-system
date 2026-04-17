"""
数据导入脚本 - 将JSON数据导入PostgreSQL数据库
"""
import os
import json
from datetime import datetime
from backend.database import SessionLocal, init_db
from backend.models import TestCase, TestResult, Report, Defect


def load_json(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_test_cases(db, data_dir):
    """导入测试用例"""
    file_path = os.path.join(data_dir, 'testcases.json')
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return 0

    cases = load_json(file_path)
    count = 0

    for case_data in cases:
        case = TestCase(
            id=case_data.get('id'),
            name=case_data.get('name'),
            type=case_data.get('type', 'api'),
            description=case_data.get('description'),
            steps=case_data.get('steps', []),
            expected_result=case_data.get('expected_result'),
            priority=case_data.get('priority', 'medium'),
            status=case_data.get('status', 'pending'),
            test_data=case_data.get('test_data'),
        )

        # 解析时间
        if case_data.get('created_at'):
            case.created_at = datetime.strptime(case_data['created_at'], '%Y-%m-%d %H:%M:%S')
        if case_data.get('updated_at'):
            case.updated_at = datetime.strptime(case_data['updated_at'], '%Y-%m-%d %H:%M:%S')

        db.add(case)
        count += 1

    db.commit()
    print(f"导入 {count} 条测试用例")
    return count


def import_test_results(db, data_dir):
    """导入测试结果"""
    file_path = os.path.join(data_dir, 'test_results.json')
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return 0

    results = load_json(file_path)
    count = 0

    for result_data in results:
        result = TestResult(
            id=result_data.get('id'),
            case_id=result_data.get('case_id'),
            case_name=result_data.get('case_name'),
            case_type=result_data.get('case_type'),
            status=result_data.get('status', 'skipped'),
            duration=result_data.get('duration', 0.0),
            steps_result=result_data.get('steps_result', []),
            error=result_data.get('error'),
        )

        # 解析时间
        if result_data.get('start_time'):
            result.start_time = datetime.strptime(result_data['start_time'], '%Y-%m-%d %H:%M:%S')
        if result_data.get('end_time'):
            result.end_time = datetime.strptime(result_data['end_time'], '%Y-%m-%d %H:%M:%S')

        db.add(result)
        count += 1

    db.commit()
    print(f"导入 {count} 条测试结果")
    return count


def import_reports(db, data_dir):
    """导入测试报告和缺陷"""
    file_path = os.path.join(data_dir, 'reports', 'report_records.json')
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return 0

    reports_data = load_json(file_path)
    report_count = 0
    defect_count = 0

    for report_data in reports_data:
        # 创建报告
        report = Report(
            id=report_data.get('id'),
            project_name=report_data.get('project_name'),
            conclusion=report_data.get('conclusion'),
            overview=report_data.get('overview'),
            focus_points=report_data.get('focus_points', []),
            risks=report_data.get('risks', []),
            test_scope=report_data.get('test_scope', []),
            test_time=report_data.get('test_time'),
            team=report_data.get('team'),
            test_device=report_data.get('test_device'),
            total_bugs=report_data.get('total_bugs', 0),
            by_category=report_data.get('by_category'),
            by_severity=report_data.get('by_severity'),
            by_handler=report_data.get('by_handler'),
            by_status=report_data.get('by_status'),
        )
        db.add(report)

        # 导入关联的缺陷
        for defect_data in report_data.get('defect_list', []):
            defect = Defect(
                id=f"{report.id}_defect_{defect_data.get('id', defect_count)}",
                number=defect_data.get('id'),
                title=defect_data.get('title'),
                module=defect_data.get('module'),
                category=defect_data.get('category'),
                severity=defect_data.get('severity'),
                status=defect_data.get('status'),
                handler=defect_data.get('handler'),
                verifier=defect_data.get('verifier'),
                reason=defect_data.get('reason'),
                reason_category=defect_data.get('reason_category'),
                version=defect_data.get('version'),
                project_name=defect_data.get('project_name'),
                steps=defect_data.get('steps'),
                expected_result=defect_data.get('expected_result'),
                actual_result=defect_data.get('actual_result'),
                report_id=report.id,
            )
            db.add(defect)
            defect_count += 1

        report_count += 1

    db.commit()
    print(f"导入 {report_count} 条报告和 {defect_count} 条缺陷")
    return report_count


def import_all():
    """导入所有数据"""
    print("=" * 50)
    print("开始导入数据到 PostgreSQL 数据库")
    print("=" * 50)

    # 初始化数据库表
    print("\n初始化数据库表...")
    init_db()
    print("数据库表创建完成")

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 获取数据目录
        data_dir = os.path.join(os.path.dirname(__file__), 'data')

        print("\n开始导入数据...")
        import_test_cases(db, data_dir)
        import_test_results(db, data_dir)
        import_reports(db, data_dir)

        print("\n" + "=" * 50)
        print("数据导入完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n导入出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import_all()