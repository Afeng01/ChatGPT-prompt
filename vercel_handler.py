from mangum import Mangum
from app import app

# 配置 Mangum 处理程序
handler = Mangum(app, lifespan="off")

# 确保应用可以在 Vercel 环境中运行
if hasattr(app, 'debug'):
    app.debug = False  # 生产环境禁用调试模式