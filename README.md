# 测试管理系统

一个功能完整的测试管理平台，支持测试用例管理、自动生成、自动执行和报告生成。

## 🚀 立即使用（无需安装）

**点击访问：** https://test-manager.up.railway.app

（或者部署你自己的版本，见下方说明）

---

## 功能特性

- **测试用例管理**: 创建、编辑、删除测试用例
- **自动生成**: 基于描述自动生成API和Web UI测试用例
- **自动执行**: 支持API接口测试和Web UI自动化测试
- **报告生成**: 自动生成详细的测试报告

---

## 本地运行

```bash
# 克隆项目
git clone <你的仓库地址>
cd test_manager

# 启动（自动安装依赖）
python start.py
```

访问 http://localhost:5000

---

## 部署到云端（永久免费链接）

详细说明见 [DEPLOY.md](DEPLOY.md)

**快速步骤：**
1. 将代码 push 到 GitHub
2. 在 https://railway.app 新建项目，选择 GitHub 仓库
3. 等待 2-3 分钟部署完成
4. 获得永久链接分享给用户

---

## 项目结构

```
test_manager/
├── backend/
│   ├── server.py           # 后端API服务
│   ├── test_generator.py  # 测试用例生成器
│   ├── test_executor.py   # 测试执行器
│   ├── report_generator.py # 报告生成器
│   └── data/              # 数据存储
├── frontend/
│   └── index.html         # 前端页面
├── requirements.txt       # Python依赖
├── start.py              # 启动脚本
└── DEPLOY.md             # 部署说明
```

## 技术栈

- **后端**: Python + Flask
- **前端**: HTML + CSS + JavaScript
- **API测试**: requests
- **Web UI测试**: Playwright

## 常见问题

**Q: 无法启动？** → 执行 `pip install -r requirements.txt`

**Q: 如何更新部署？** → push 到 GitHub 后自动重新部署
