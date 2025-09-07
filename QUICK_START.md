# 快速部署指南

## 🚀 一键部署（推荐）

### 步骤1：克隆项目
```bash
git clone https://github.com/mysticfreely/bank-screenshot-ocr-lightweight.git
cd bank-screenshot-ocr-lightweight
```

### 步骤2：选择部署方式

#### 方式A：Docker部署（推荐）
```bash
# 构建镜像
docker build -f Dockerfile.lightweight -t bank-ocr-lightweight .

# 运行容器
docker run -d \
  --name bank-ocr \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/config:/app/config \
  bank-ocr-lightweight
```

#### 方式B：Docker Compose部署
```bash
docker-compose -f docker-compose.lightweight.yml up -d
```

#### 方式C：Python本地部署
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.lightweight.txt

# 创建必要目录
mkdir -p config uploads results logs

# 创建默认配置文件
cat > config/api_config.json << 'EOF'
{
  "ocr_apis": {
    "baidu": {
      "enabled": false,
      "api_key": "",
      "secret_key": "",
      "url": "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
      "confidence_threshold": 0.8
    },
    "azure": {
      "enabled": false,
      "subscription_key": "",
      "endpoint": "",
      "confidence_threshold": 0.8
    },
    "google": {
      "enabled": false,
      "api_key": "",
      "confidence_threshold": 0.8
    }
  },
  "image_preprocessing": {
    "max_size": 4096,
    "quality": 85,
    "format": "JPEG"
  }
}
EOF

# 启动应用
python enterprise_app.py
```

### 步骤3：访问系统
打开浏览器访问：http://localhost:5000

### 步骤4：配置API（必需）
1. 访问：http://localhost:5000/admin/api-config
2. 选择一个OCR服务商并配置API密钥
3. 测试连接确保配置正确

## 🔧 常见问题解决

### 问题1：Docker构建失败
**错误**：`COPY config/ config/` 失败
**解决**：使用最新的Dockerfile.lightweight，它会自动创建config目录

### 问题2：端口被占用
**错误**：`port 5000 already in use`
**解决**：
```bash
# 查看占用端口的进程
lsof -i :5000
# 或者使用其他端口
docker run -p 8080:5000 ...
```

### 问题3：权限问题
**错误**：`Permission denied`
**解决**：
```bash
# 给脚本执行权限
chmod +x deploy.sh
# 或者使用sudo运行Docker命令
sudo docker ...
```

### 问题4：模块导入错误
**错误**：`ModuleNotFoundError`
**解决**：确保安装了所有依赖
```bash
pip install -r requirements.lightweight.txt
```

## 📋 API配置指南

### 百度OCR（推荐新手）
1. 访问：https://cloud.baidu.com/product/ocr
2. 注册并创建应用
3. 获取API Key和Secret Key
4. 在系统中配置并测试

### Azure OCR（推荐企业）
1. 访问：https://azure.microsoft.com/services/cognitive-services/
2. 创建Computer Vision资源
3. 获取订阅密钥和端点
4. 在系统中配置并测试

### Google OCR（最高精度）
1. 访问：https://cloud.google.com/vision
2. 启用Vision API
3. 创建API密钥
4. 在系统中配置并测试

## 🎯 测试步骤

1. **上传测试图片**：访问 http://localhost:5000/upload
2. **选择银行截图文件**（支持PNG、JPG等格式）
3. **点击处理**，等待识别完成
4. **查看结果**，下载Excel或HTML报告
5. **检查准确性**，如有问题调整API配置

## 📞 获取帮助

- **查看日志**：`docker logs bank-ocr` 或 `tail -f logs/app.log`
- **重启服务**：`docker restart bank-ocr`
- **停止服务**：`docker stop bank-ocr`
- **清理重建**：`docker rm bank-ocr && docker rmi bank-ocr-lightweight`

## ✅ 部署成功标志

- ✅ 浏览器能访问 http://localhost:5000
- ✅ 管理页面正常显示
- ✅ API配置页面可以打开
- ✅ 能够上传图片并获得识别结果

---

**如果遇到其他问题，请提供错误日志以便进一步诊断。**