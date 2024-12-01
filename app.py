from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_pymongo import PyMongo
from datetime import datetime
import pytz
import os
import logging
import certifi
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
from pymongo import MongoClient

# 配置日志 - 设置更详细的日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.debug = True  # 启用调试模式

# MongoDB配置
mongo_uri = os.getenv('MONGODB_URI')
app.logger.debug(f"MongoDB URI: {mongo_uri.replace(os.getenv('MONGODB_PASSWORD', ''), '***')}")

try:
    # 直接连接到指定的数据库
    client = MongoClient(mongo_uri)
    db = client.promptdb  # 直接使用数据库名称
    
    # 确保索引存在
    db.prompts.create_index([('title', 'text'), ('content', 'text'), ('category', 'text')])
    
except Exception as e:
    app.logger.error(f"MongoDB Atlas 连接错误: {str(e)}", exc_info=True)
    raise

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# 从环境变量获取管理员IP地址列表
ADMIN_IPS = set(os.getenv('ADMIN_IPS', '127.0.0.1').split(','))
logger.info(f"管理员IP列表: {ADMIN_IPS}")

def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    logger.debug(f"客户端IP: {ip}")
    return ip

def can_edit(prompt, ip):
    """检查是否有权限编辑"""
    has_permission = ip in ADMIN_IPS or ip == prompt.get('creator_ip')
    logger.debug(f"权限检查 - IP: {ip}, 是否有权限: {has_permission}")
    return has_permission

@app.route('/')
def index():
    try:
        logger.debug("访问首页")
        prompts = list(db.prompts.find())
        categorized_prompts = {}
        current_ip = get_client_ip()
        
        for prompt in prompts:
            prompt['id'] = str(prompt['_id'])
            categories = [cat.strip() for cat in prompt.get('category', '').replace('，', ',').split(',') if cat.strip()]
            for category in categories:
                if category not in categorized_prompts:
                    categorized_prompts[category] = []
                categorized_prompts[category].append(prompt)
        
        sorted_categories = sorted(categorized_prompts.keys())
        is_admin = current_ip in ADMIN_IPS
        
        logger.debug(f"首页加载成功 - 分类数: {len(sorted_categories)}, 是否管理员: {is_admin}")
        return render_template('index.html', 
                             categorized_prompts=categorized_prompts, 
                             categories=sorted_categories,
                             current_ip=current_ip,
                             is_admin=is_admin)
    except Exception as e:
        logger.error(f"首页加载错误: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/add', methods=['GET', 'POST'])
def add_prompt():
    try:
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
            
            db.prompts.insert_one(new_prompt)
            logger.info(f"新Prompt添加成功 - 标题: {title}")
            return redirect(url_for('index'))
        
        return render_template('add.html')
    except Exception as e:
        logger.error(f"添加Prompt错误: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit_prompt(id):
    try:
        prompt = db.prompts.find_one({'_id': ObjectId(id)})
        if not prompt:
            logger.warning(f"Prompt不存在 - ID: {id}")
            flash('Prompt不存在')
            return redirect(url_for('index'))
        
        current_ip = get_client_ip()
        if not can_edit(prompt, current_ip):
            logger.warning(f"编辑权限被拒绝 - IP: {current_ip}, Prompt ID: {id}")
            flash('您没有权限编辑此内容')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            db.prompts.update_one(
                {'_id': ObjectId(id)},
                {'$set': {
                    'title': request.form.get('title'),
                    'content': request.form.get('content'),
                    'category': request.form.get('category')
                }}
            )
            logger.info(f"Prompt更新成��� - ID: {id}")
            return redirect(url_for('index'))
        
        return render_template('edit.html', prompt=prompt)
    except Exception as e:
        logger.error(f"编辑Prompt错误: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/delete/<string:id>', methods=['POST'])
def delete_prompt(id):
    try:
        prompt = db.prompts.find_one({'_id': ObjectId(id)})
        if not prompt:
            logger.warning(f"Prompt不存在 - ID: {id}")
            flash('Prompt不存在')
            return redirect(url_for('index'))
        
        current_ip = get_client_ip()
        if not can_edit(prompt, current_ip):
            logger.warning(f"删除权限被拒绝 - IP: {current_ip}, Prompt ID: {id}")
            flash('您没有权限删除此内容')
            return redirect(url_for('index'))
        
        db.prompts.delete_one({'_id': ObjectId(id)})
        logger.info(f"Prompt删除成功 - ID: {id}")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"删除Prompt错误: {e}")
        return render_template('error.html', error=str(e)), 500

# 添加日期格式化过滤器
@app.template_filter('format_datetime')
def format_datetime(value):
    """格式化日期时间"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return value

# 错误处理
@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Server Error: {error}')
    return render_template('error.html', error=error), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f'Unhandled Exception: {e}')
    return render_template('error.html', error=e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 