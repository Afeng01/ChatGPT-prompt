from app import app

def handler(event, context):
    return app

# 确保应用可以在 Vercel 环境中运行
app.debug = False  # 生产环境禁用调试模式 