from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_pymongo import PyMongo
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
from bson import ObjectId

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# MongoDB配置
app.config["MONGO_URI"] = os.getenv("MONGODB_URI", "mongodb://localhost:27017/promptdb")
mongo = PyMongo(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# 从环境变量获取管理员IP地址列表
ADMIN_IPS = set(os.getenv('ADMIN_IPS', '127.0.0.1').split(','))

def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def can_edit(prompt, ip):
    """检查是否有权限编辑"""
    return ip in ADMIN_IPS or ip == prompt.get('creator_ip')

@app.route('/')
def index():
    prompts = list(mongo.db.prompts.find())
    categorized_prompts = {}
    current_ip = get_client_ip()
    
    for prompt in prompts:
        prompt['id'] = str(prompt['_id'])  # 转换ObjectId为字符串
        categories = [cat.strip() for cat in prompt.get('category', '').replace('，', ',').split(',') if cat.strip()]
        for category in categories:
            if category not in categorized_prompts:
                categorized_prompts[category] = []
            categorized_prompts[category].append(prompt)
    
    sorted_categories = sorted(categorized_prompts.keys())
    is_admin = current_ip in ADMIN_IPS
    
    return render_template('index.html', 
                         categorized_prompts=categorized_prompts, 
                         categories=sorted_categories,
                         current_ip=current_ip,
                         is_admin=is_admin)

@app.route('/add', methods=['GET', 'POST'])
def add_prompt():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        creator_ip = get_client_ip()
        
        new_prompt = {
            'title': title,
            'content': content,
            'category': category,
            'creator_ip': creator_ip,
            'created_at': datetime.now(pytz.timezone('Asia/Shanghai'))
        }
        
        mongo.db.prompts.insert_one(new_prompt)
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit_prompt(id):
    prompt = mongo.db.prompts.find_one({'_id': ObjectId(id)})
    if not prompt:
        flash('Prompt不存在')
        return redirect(url_for('index'))
    
    current_ip = get_client_ip()
    if not can_edit(prompt, current_ip):
        flash('您没有权限编辑此内容')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        mongo.db.prompts.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'title': request.form.get('title'),
                'content': request.form.get('content'),
                'category': request.form.get('category')
            }}
        )
        return redirect(url_for('index'))
    
    return render_template('edit.html', prompt=prompt)

@app.route('/delete/<string:id>', methods=['POST'])
def delete_prompt(id):
    prompt = mongo.db.prompts.find_one({'_id': ObjectId(id)})
    if not prompt:
        flash('Prompt不存在')
        return redirect(url_for('index'))
    
    current_ip = get_client_ip()
    if not can_edit(prompt, current_ip):
        flash('您没有权限删除此内容')
        return redirect(url_for('index'))
    
    mongo.db.prompts.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('index'))

# 添加日期格式化过滤器
@app.template_filter('format_datetime')
def format_datetime(value):
    """格式化日期时间"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return value

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 