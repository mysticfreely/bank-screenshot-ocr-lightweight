#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级银行截图OCR处理Web应用 - 修复版
支持轻量级OCR处理器和API配置管理
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from lightweight_ocr_processor import LightweightOCRProcessor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中请更改

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs('config', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('templates/admin', exist_ok=True)
os.makedirs('templates/errors', exist_ok=True)

def create_basic_templates():
    """创建基本模板文件"""
    templates_dir = 'templates'
    
    # 基础模板
    base_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}银行截图OCR处理系统{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .navbar { background-color: #007bff; padding: 10px 0; margin-bottom: 20px; }
        .navbar a { color: white; text-decoration: none; margin: 0 15px; }
        .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 4px; }
        .alert-success { background-color: #d4edda; color: #155724; }
        .alert-error { background-color: #f8d7da; color: #721c24; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="container">
            <a href="{{ url_for('index') }}">首页</a>
            <a href="{{ url_for('upload_files') }}">上传处理</a>
            <a href="{{ url_for('admin_dashboard') }}">管理后台</a>
        </div>
    </div>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
    '''
    
    # 首页模板
    index_template = '''
{% extends "base.html" %}

{% block content %}
<h1>银行截图OCR处理系统 - 轻量版</h1>
<p>基于第三方API调用，内存占用小，部署简单</p>

<div style="display: flex; gap: 20px; margin-top: 30px;">
    <div class="card">
        <h3>🚀 轻量化设计</h3>
        <p>基于API调用，内存占用仅300MB</p>
    </div>
    <div class="card">
        <h3>🔧 多API支持</h3>
        <p>支持百度、Azure、Google等OCR服务</p>
    </div>
    <div class="card">
        <h3>📊 智能识别</h3>
        <p>自动识别银行信息</p>
    </div>
</div>

<div style="text-align: center; margin-top: 30px;">
    <a href="{{ url_for('upload_files') }}" class="btn">开始处理</a>
    <a href="{{ url_for('admin_dashboard') }}" class="btn">管理后台</a>
</div>
{% endblock %}
    '''
    
    # 上传页面模板
    upload_template = '''
{% extends "base.html" %}

{% block content %}
<h2>上传银行截图</h2>
<form method="POST" enctype="multipart/form-data">
    <div style="margin: 20px 0;">
        <label for="files">选择图片文件:</label><br>
        <input type="file" name="files" multiple accept=".png,.jpg,.jpeg,.gif,.bmp,.tiff" required>
    </div>
    <button type="submit" class="btn">开始处理</button>
</form>
{% endblock %}
    '''
    
    # 结果页面模板
    results_template = '''
{% extends "base.html" %}

{% block content %}
<h2>处理结果</h2>
<div style="margin: 20px 0;">
    <a href="{{ url_for('download_file', filename=excel_file) }}" class="btn">下载Excel</a>
    <a href="{{ url_for('download_file', filename=html_file) }}" class="btn">下载HTML</a>
</div>

<table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
    <tr style="background-color: #f2f2f2;">
        <th style="border: 1px solid #ddd; padding: 8px;">文件</th>
        <th style="border: 1px solid #ddd; padding: 8px;">银行名称</th>
        <th style="border: 1px solid #ddd; padding: 8px;">公司名称</th>
        <th style="border: 1px solid #ddd; padding: 8px;">账号</th>
        <th style="border: 1px solid #ddd; padding: 8px;">余额</th>
        <th style="border: 1px solid #ddd; padding: 8px;">状态</th>
    </tr>
    {% for result in results %}
    <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.image_path.split('/')[-1] }}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.bank_name or '' }}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.company_name or '' }}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.account_number or '' }}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.balance or '' }}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{ result.status }}</td>
    </tr>
    {% endfor %}
</table>
{% endblock %}
    '''
    
    # 管理后台模板
    admin_template = '''
{% extends "base.html" %}

{% block content %}
<h2>管理后台</h2>
<div class="card">
    <h3>API状态</h3>
    {% for provider, status in api_status.items() %}
    <p><strong>{{ provider.upper() }}:</strong> 
        {% if status.enabled %}
            <span style="color: green;">已启用</span>
        {% else %}
            <span style="color: red;">未启用</span>
        {% endif %}
        {% if status.configured %}
            (已配置)
        {% else %}
            (未配置)
        {% endif %}
    </p>
    {% endfor %}
</div>

<div style="margin-top: 20px;">
    <a href="{{ url_for('api_config') }}" class="btn">API配置</a>
</div>
{% endblock %}
    '''
    
    # 404错误页面
    error_404_template = '''
{% extends "base.html" %}

{% block content %}
<h2>页面未找到</h2>
<p>抱歉，您访问的页面不存在。</p>
<a href="{{ url_for('index') }}" class="btn">返回首页</a>
{% endblock %}
    '''
    
    # 500错误页面
    error_500_template = '''
{% extends "base.html" %}

{% block content %}
<h2>服务器错误</h2>
<p>抱歉，服务器遇到了问题。</p>
<a href="{{ url_for('index') }}" class="btn">返回首页</a>
{% endblock %}
    '''
    
    # 保存所有模板
    templates = {
        'base.html': base_template,
        'index.html': index_template,
        'upload.html': upload_template,
        'results.html': results_template,
        'admin/dashboard.html': admin_template,
        'errors/404.html': error_404_template,
        'errors/500.html': error_500_template
    }
    
    for template_path, content in templates.items():
        full_path = os.path.join(templates_dir, template_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("基本模板文件已创建")

# 初始化OCR处理器
ocr_processor = LightweightOCRProcessor()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """文件上传页面"""
    if request.method == 'POST':
        try:
            if 'files' not in request.files:
                flash('没有选择文件', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                flash('没有选择文件', 'error')
                return redirect(request.url)
            
            uploaded_files = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    uploaded_files.append(filepath)
                else:
                    flash(f'文件 {file.filename} 格式不支持', 'error')
            
            if not uploaded_files:
                flash('没有有效的图片文件', 'error')
                return redirect(request.url)
            
            results = ocr_processor.process_multiple_images(uploaded_files)
            
            session_id = str(uuid.uuid4())
            excel_path = os.path.join(RESULTS_FOLDER, f'results_{session_id}.xlsx')
            html_path = os.path.join(RESULTS_FOLDER, f'results_{session_id}.html')
            
            ocr_processor.export_to_excel(excel_path)
            ocr_processor.export_to_html(html_path)
            
            return render_template('results.html', 
                                 results=results,
                                 excel_file=f'results_{session_id}.xlsx',
                                 html_file=f'results_{session_id}.html')
            
        except Exception as e:
            logger.error(f"处理上传文件时出错: {e}")
            flash(f'处理文件时出错: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/admin')
def admin_dashboard():
    """管理员仪表板"""
    api_status = ocr_processor.get_api_status()
    return render_template('admin/dashboard.html', api_status=api_status)

@app.route('/admin/api-config')
def api_config():
    """API配置页面"""
    current_config = ocr_processor.config['ocr_apis']
    return render_template('admin/api_config.html', config=current_config)

@app.route('/admin/api-config/update', methods=['POST'])
def update_api_config():
    """更新API配置"""
    try:
        provider = request.form.get('provider')
        if not provider:
            return jsonify({'success': False, 'message': '未指定API提供商'})
        
        config_data = {
            'enabled': request.form.get('enabled') == 'on'
        }
        
        if provider == 'baidu':
            config_data.update({
                'api_key': request.form.get('api_key', ''),
                'secret_key': request.form.get('secret_key', ''),
                'confidence_threshold': float(request.form.get('confidence_threshold', 0.8))
            })
        elif provider == 'azure':
            config_data.update({
                'subscription_key': request.form.get('subscription_key', ''),
                'endpoint': request.form.get('endpoint', ''),
                'confidence_threshold': float(request.form.get('confidence_threshold', 0.8))
            })
        elif provider == 'google':
            config_data.update({
                'api_key': request.form.get('api_key', ''),
                'confidence_threshold': float(request.form.get('confidence_threshold', 0.8))
            })
        
        success = ocr_processor.update_api_config(provider, config_data)
        
        if success:
            flash(f'{provider.upper()} API配置已更新', 'success')
            return redirect(url_for('api_config'))
        else:
            flash('配置更新失败', 'error')
            return redirect(url_for('api_config'))
            
    except Exception as e:
        logger.error(f"更新API配置时出错: {e}")
        flash(f'更新配置时出错: {str(e)}', 'error')
        return redirect(url_for('api_config'))

@app.route('/download/<filename>')
def download_file(filename):
    """下载结果文件"""
    try:
        file_path = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('文件不存在', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"下载文件时出错: {e}")
        flash(f'下载失败: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """获取API状态"""
    try:
        status = ocr_processor.get_api_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"获取API状态时出错: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # 创建基本模板文件
    create_basic_templates()
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=False)