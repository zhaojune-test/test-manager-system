# 部署到 Railway.app（永久免费链接）

## 快速部署（3分钟完成）

### 步骤 1: 上传代码到 GitHub

**方式 A（推荐）：使用工具**
1. 双击运行 `deploy_to_github.bat`
2. 按提示完成 GitHub 授权
3. 等待上传完成

**方式 B：手动**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/test-manager.git
git push -u origin main
```

### 步骤 2: 部署到 Railway

1. 打开 https://railway.app并登录（用 GitHub 账号）
2. 点击 **"New Project"** → **"Deploy from GitHub"**
3. 选择 `test-manager` 仓库
4. 等待 2-3 分钟部署完成
5. 获得永久链接：`https://test-manager.up.railway.app`

### 步骤 3: 分享使用

- 将链接分享给任何人
- 用户打开即可使用，无需安装任何软件

---

## 本地运行

```bash
pip install -r requirements.txt
python start.py
```
访问 http://localhost:5000

---

## 常见问题

**Q: 部署失败？** → 确保 GitHub 仓库包含 `requirements.txt`

**Q: 如何更新？** → push 到 GitHub 后 Railway 自动重新部署

**Q: 链接过期？** → Railway 免费链接永久有效

**Q: 免费额度？** → 每月 500 小时，1 个应用足够
