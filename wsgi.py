from app import app

# 本地开发时使用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
# Vercel serverless 函数入口
def handler(event, context):
    return app 