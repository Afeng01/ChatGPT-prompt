from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from itertools import groupby
import pytz
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 禁用 SQLAlchemy 的文件系统访问
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False}
}

# 在 Vercel 环境中使用内存数据库
if os.environ.get('VERCEL_ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prompts.db'

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# 从环境变量获取管理员IP地址列表
ADMIN_IPS = set(os.getenv('ADMIN_IPS', '127.0.0.1').split(','))

db = SQLAlchemy(app)

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    creator_ip = db.Column(db.String(50))

    def format_created_at(self):
        """格式化创建时间为中国时区"""
        if self.created_at.tzinfo is None:
            china_tz = pytz.timezone('Asia/Shanghai')
            return self.created_at.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M')
        return self.created_at.strftime('%Y-%m-%d %H:%M')

    def can_edit(self, ip):
        """检查是否有权限编辑"""
        return ip in ADMIN_IPS or ip == self.creator_ip

# 初始化数据库
with app.app_context():
    db.create_all()
    # 如果数据库是空的，添加示例数据
    if not Prompt.query.first():
        sample_prompts = [
            Prompt(
                title="示例Prompt",
                content="这是一个示例Prompt，用于测试显示效果。",
                category="示例,测试",
                creator_ip="127.0.0.1"
            )
        ]
        db.session.add_all(sample_prompts)
        db.session.commit()

def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

@app.route('/')
def index():
    prompts = Prompt.query.order_by(Prompt.category).all()
    categorized_prompts = {}
    current_ip = get_client_ip()
    
    for prompt in prompts:
        categories = [cat.strip() for cat in prompt.category.replace('，', ',').split(',') if cat.strip()]
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
        
        new_prompt = Prompt(
            title=title, 
            content=content, 
            category=category,
            creator_ip=creator_ip
        )
        db.session.add(new_prompt)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_prompt(id):
    prompt = Prompt.query.get_or_404(id)
    current_ip = get_client_ip()
    
    if not prompt.can_edit(current_ip):
        flash('您没有权限编辑此内容')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        prompt.title = request.form.get('title')
        prompt.content = request.form.get('content')
        prompt.category = request.form.get('category')
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit.html', prompt=prompt)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_prompt(id):
    prompt = Prompt.query.get_or_404(id)
    current_ip = get_client_ip()
    
    if not prompt.can_edit(current_ip):
        flash('您没有权限删除此内容')
        return redirect(url_for('index'))
    
    db.session.delete(prompt)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 