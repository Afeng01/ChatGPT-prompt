from app import app

def handler(event, context):
    """Handle Vercel serverless function requests"""
    from mangum import Mangum
    
    handler = Mangum(app, lifespan="off")
    return handler(event, context)

# 确保应用可以在 Vercel 环境中运行
app.debug = False  # 生产环境禁用调试模式