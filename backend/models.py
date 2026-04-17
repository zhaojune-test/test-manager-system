"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from backend.database import Base


class CaseTypeEnum(enum.Enum):
    """用例类型枚举"""
    API = "api"
    UI = "ui"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"


class CaseStatusEnum(enum.Enum):
    """用例状态枚举"""
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"


class TestResultStatusEnum(enum.Enum):
    """测试结果状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class DefectSeverityEnum(enum.Enum):
    """缺陷严重程度枚举"""
    FATAL = "致命"
    SEVERE = "严重"
    GENERAL = "一般"
    MINOR = "轻微"


class DefectStatusEnum(enum.Enum):
    """缺陷状态枚举"""
    PENDING = "待处理"
    PROCESSING = "处理中"
    FIXED = "已修复"
    WONT_FIX = "暂不修复"
    CLOSED = "已关闭"
    REOPENED = "再次打开"


class TestCase(Base):
    """测试用例模型"""
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), default="api")
    description = Column(Text)
    steps = Column(JSON)  # 存储步骤列表
    expected_result = Column(Text)
    priority = Column(String(50), default="medium")  # high, medium, low
    status = Column(String(50), default="pending")
    test_data = Column(JSON)  # 存储测试数据配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")


class TestResult(Base):
    """测试结果模型"""
    __tablename__ = "test_results"

    id = Column(String(36), primary_key=True)
    case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    case_name = Column(String(255))
    case_type = Column(String(50))
    status = Column(String(50), nullable=False)  # passed, failed, skipped, error
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float, default=0.0)
    steps_result = Column(JSON)  # 存储步骤执行结果
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    test_case = relationship("TestCase", back_populates="results")


class Defect(Base):
    """缺陷模型"""
    __tablename__ = "defects"

    id = Column(String(36), primary_key=True)
    number = Column(String(50))  # 缺陷编号
    title = Column(String(500), nullable=False)
    module = Column(String(255))
    category = Column(String(100))  # 功能错误, UI问题, 性能问题等
    severity = Column(String(50))  # 致命, 严重, 一般, 轻微
    status = Column(String(50))  # 待处理, 处理中, 已修复等
    handler = Column(String(100))  # 处理人
    verifier = Column(String(100))  # 验证人
    reason = Column(Text)  # 缺陷原因
    reason_category = Column(String(100))  # 原因分类
    pm = Column(String(100))  # 产品经理
    version = Column(String(100))  # 版本
    project_name = Column(String(255))  # 项目名称
    steps = Column(Text)  # 操作步骤
    expected_result = Column(Text)  # 预期结果
    actual_result = Column(Text)  # 实际结果
    create_time = Column(DateTime)
    close_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=True)


class Report(Base):
    """测试报告模型"""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    project_name = Column(String(255))
    conclusion = Column(Text)
    overview = Column(Text)
    focus_points = Column(JSON)  # 重点关注
    risks = Column(JSON)  # 风险项
    test_scope = Column(JSON)  # 测试范围
    test_time = Column(String(100))
    team = Column(JSON)  # 团队成员
    test_device = Column(String(255))
    total_bugs = Column(Integer, default=0)
    by_category = Column(JSON)  # 按类别统计
    by_severity = Column(JSON)  # 按严重程度统计
    by_handler = Column(JSON)  # 按处理人统计
    by_status = Column(JSON)  # 按状态统计
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    defects = relationship("Defect", back_populates="report", cascade="all, delete-orphan")
