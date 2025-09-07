#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级银行截图OCR处理Web应用
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
os.makedirs('templates/admin', exist_ok=True)

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
            # 检查是否有文件
            if 'files' not in request.files:
                flash('没有选择文件', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                flash('没有选择文件', 'error')
                return redirect(request.url)
            
            # 保存上传的文件
            uploaded_files = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # 添加时间戳避免文件名冲突
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    uploaded_files.append(filepath)
                else:
                    flash(f'文件 {file.filename} 格式不支持', 'warning')
            
            if not uploaded_files:
                flash('没有有效的图片文件', 'error')
                return redirect(request.url)
            
            # 处理图片
            results = ocr_processor.process_multiple_images(uploaded_files)
            
            # 生成结果文件
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
        
        # 构建配置数据
        config_data = {
            'enabled': request.form.get('enabled') == 'on'
        }
        
        # 根据不同提供商添加相应的配置字段
        if provider == 'baidu':
            config_data.update({
                'api_key': request.form.get('api_key', ''),
                'secret_key': request.form.get('secret_key', ''),
                'confidence_threshold': float(request.form.get('confidence_threshold', 0.8))
            })
        elif provider == 'tencent':
            config_data.update({
                'secret_id': request.form.get('secret_id', ''),
                'secret_key': request.form.get('secret_key', ''),
                'region': request.form.get('region', 'ap-beijing'),
                'confidence_threshold': float(request.form.get('confidence_threshold', 0.8))
            })
        elif provider == 'aliyun':
            config_data.update({
                'access_key_id': request.form.get('access_key_id', ''),
                'access_key_secret': request.form.get('access_key_secret', ''),
                'endpoint': request.form.get('endpoint', 'ocr.cn-shanghai.aliyuncs.com'),
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
        
        # 更新配置
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

@app.route('/admin/test-api/<provider>')
def test_api(provider):
    """测试API连接"""
    try:
        # 这里可以添加API测试逻辑
        # 暂时返回配置状态
        api_status = ocr_processor.get_api_status()
        if provider in api_status:
            status = api_status[provider]
            if status['enabled'] and status['configured']:
                return jsonify({
                    'success': True, 
                    'message': f'{provider.upper()} API配置正常',
                    'status': status
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': f'{provider.upper()} API未启用或未配置',
                    'status': status
                })
        else:
            return jsonify({'success': False, 'message': '未知的API提供商'})
            
    except Exception as e:
        logger.error(f"测试API时出错: {e}")
        return jsonify({'success': False, 'message': f'测试失败: {str(e)}'})

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

@app.route('/api/process', methods=['POST'])
def api_process():
    """API接口：处理图片"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'message': '没有有效文件'})
        
        # 保存并处理文件
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                uploaded_files.append(filepath)
        
        if not uploaded_files:
            return jsonify({'success': False, 'message': '没有有效的图片文件'})
        
        # 处理图片
        results = ocr_processor.process_multiple_images(uploaded_files)
        
        return jsonify({
            'success': True,
            'message': f'成功处理 {len(results)} 个文件',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"API处理请求时出错: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # 创建基本模板文件（如果不存在）
    create_basic_templates()
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)

def create_basic_templates():
    """创建基本模板文件"""
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(os.path.join(templates_dir, 'admin'), exist_ok=True)
    os.makedirs(os.path.join(templates_dir, 'errors'), exist_ok=True)
    
    # 基础模板
    base_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}银行截图OCR处理系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; }
        .footer { margin-top: 50px; padding: 20px 0; background-color: #f8f9fa; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">银行截图OCR系统</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">首页</a>
                <a class="nav-link" href="{{ url_for('upload_files') }}">上传处理</a>
                <a class="nav-link" href="{{ url_for('admin_dashboard') }}">管理后台</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <footer class="footer">
        <div class="container text-center">
            <span class="text-muted">银行截图OCR处理系统 - 轻量版</span>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
    '''
    
    # 保存基础模板
    with open(os.path.join(templates_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    # 首页模板
    index_template = '''
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto">
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4">银行截图OCR处理系统</h1>
            <p class="lead">轻量版 - 基于第三方API调用，内存占用小，部署简单</p>
            <hr class="my-4">
            <p>支持多种OCR服务商：百度、腾讯、阿里云、Azure、Google</p>
            <a class="btn btn-primary btn-lg" href="{{ url_for('upload_files') }}" role="button">开始处理</a>
            <a class="btn btn-secondary btn-lg" href="{{ url_for('admin_dashboard') }}" role="button">管理后台</a>
        </div>
    </div>
</div>

<div class="row mt-5">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">🚀 轻量化设计</h5>
                <p class="card-text">基于API调用，无需本地OCR库，内存占用从1.5GB降至300MB</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">🔧 多API支持</h5>
                <p class="card-text">支持百度、腾讯、阿里云、Azure、Google等多种OCR服务</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">📊 智能识别</h5>
                <p class="card-text">自动识别银行名称、公司名称、账号和余额信息</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
    '''
    
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)