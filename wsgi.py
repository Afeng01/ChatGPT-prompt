from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
# Vercel serverless 函数入口
def app_handler(event, context):
    return app.wsgi_app 