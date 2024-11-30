# ChatGPT Prompts 库

一个用于存储和分享ChatGPT Prompts的网站。

## 功能特点

- 按分类组织Prompts
- 支持多分类标签
- 一键复制Prompt内容
- 用户权限管理
- 响应式设计

## 本地开发

1. 克隆仓库：
```bash
git clone [你的仓库URL]
cd [仓库名称]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
- 复制 `.env.example` 为 `.env`
- 修改 `.env` 中的配置

4. 运行应用：
```bash
python app.py
```

## 部署说明

本项目使用Vercel部署。部署时需要设置以下环境变量：

- `SECRET_KEY`: 用于会话安全
- `ADMIN_IPS`: 管理员IP地址列表（逗号分隔）

## 技术栈

- Flask
- SQLite
- Bootstrap 5
- Python 3.x 