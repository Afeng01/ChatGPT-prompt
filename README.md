# ChatGPT Prompts 库

一个简单的 ChatGPT Prompts 展示网站，收集和分享高质量的 Prompts。

## 特点

- 纯静态网站，无需后端服务器
- 按分类展示 Prompts
- 支持一键复制 Prompt
- 响应式设计，支持移动端

## 如何更新内容

1. 修改 `static/data/prompts.json` 文件
2. 按照以下格式添加新的 Prompt：

```json
{
  "id": "唯一ID",
  "title": "Prompt标题",
  "content": "Prompt内容",
  "category": "分类1,分类2",
  "created_at": "创建日期"
}
```

## 部署

1. Fork 这个仓库
2. 在仓库设置中启用 GitHub Pages
3. 选择 main 分支作为源
4. 等待几分钟后访问 your-username.github.io/repository-name

## 本地开发

由于使用了 fetch API，需要通过 HTTP 服务器访问文件。可以使用以下方法之一：

1. Python 简单服务器：
```bash
python -m http.server 8000
```

2. VS Code Live Server 插件

然后访问 `http://localhost:8000` 即可。