#!/bin/bash
# 轻量级银行截图OCR处理器一键部署脚本
# 支持多种部署方式：Docker、本地Python、云服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    log_success "操作系统: $OS"
}

# 检查Docker
check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log_success "Docker已安装: $DOCKER_VERSION"
        return 0
    else
        log_warning "Docker未安装"
        return 1
    fi
}

# 检查Docker Compose
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        log_success "Docker Compose已安装: $COMPOSE_VERSION"
        return 0
    else
        log_warning "Docker Compose未安装"
        return 1
    fi
}

# 检查Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python3已安装: $PYTHON_VERSION"
        return 0
    else
        log_warning "Python3未安装"
        return 1
    fi
}

# 安装Docker（Linux）
install_docker_linux() {
    log_info "安装Docker..."
    
    # 更新包索引
    sudo apt-get update
    
    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 设置稳定版仓库
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "安装Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 添加执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 创建必要的目录
setup_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p config
    mkdir -p uploads
    mkdir -p results
    mkdir -p logs
    mkdir -p templates/admin
    
    log_success "目录创建完成"
}

# 创建默认配置文件
setup_config() {
    log_info "创建默认配置文件..."
    
    # 创建API配置文件
    cat > config/api_config.json << EOF
{
  "ocr_apis": {
    "baidu": {
      "enabled": false,
      "api_key": "",
      "secret_key": "",
      "url": "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
      "confidence_threshold": 0.8
    },
    "tencent": {
      "enabled": false,
      "secret_id": "",
      "secret_key": "",
      "region": "ap-beijing",
      "confidence_threshold": 0.8
    },
    "aliyun": {
      "enabled": false,
      "access_key_id": "",
      "access_key_secret": "",
      "endpoint": "ocr.cn-shanghai.aliyuncs.com",
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
    
    # 创建环境变量文件
    cat > .env << EOF
# 轻量级银行截图OCR处理器环境变量
FLASK_ENV=production
FLASK_APP=enterprise_app.py
SECRET_KEY=your-secret-key-here-please-change-in-production

# 数据库配置
DATABASE_PATH=公司在用银行库20250412.xlsx

# 上传配置
UPLOAD_FOLDER=uploads
RESULTS_FOLDER=results
MAX_CONTENT_LENGTH=16777216

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
    
    log_success "配置文件创建完成"
}

# Docker部署
deploy_docker() {
    log_info "使用Docker部署..."
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker build -f Dockerfile.lightweight -t bank-ocr-lightweight .
    
    # 停止现有容器
    log_info "停止现有容器..."
    docker stop bank-ocr-lightweight 2>/dev/null || true
    docker rm bank-ocr-lightweight 2>/dev/null || true
    
    # 启动容器
    log_info "启动容器..."
    docker run -d \
        --name bank-ocr-lightweight \
        -p 5000:5000 \
        -v $(pwd)/config:/app/config \
        -v $(pwd)/uploads:/app/uploads \
        -v $(pwd)/results:/app/results \
        -v $(pwd)/logs:/app/logs \
        --restart unless-stopped \
        bank-ocr-lightweight
    
    log_success "Docker部署完成"
}

# Docker Compose部署
deploy_docker_compose() {
    log_info "使用Docker Compose部署..."
    
    # 启动服务
    docker-compose -f docker-compose.lightweight.yml up -d
    
    log_success "Docker Compose部署完成"
}

# Python本地部署
deploy_python() {
    log_info "使用Python本地部署..."
    
    # 创建虚拟环境
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.lightweight.txt
    
    # 启动应用
    log_info "启动应用..."
    nohup python enterprise_app.py > logs/app.log 2>&1 &
    
    log_success "Python本地部署完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "=== 部署完成 ==="
    echo
    log_info "访问地址: http://localhost:5000"
    log_info "管理后台: http://localhost:5000/admin"
    log_info "API配置: http://localhost:5000/admin/api-config"
    echo
    log_info "重要提醒:"
    echo "  1. 请访问管理后台配置OCR API密钥"
    echo "  2. 上传银行数据库文件到根目录"
    echo "  3. 检查防火墙设置，确保端口5000可访问"
    echo "  4. 生产环境请修改默认密钥"
    echo
    log_info "日志文件: logs/app.log"
    log_info "配置文件: config/api_config.json"
}

# 主菜单
show_menu() {
    echo
    echo "=== 轻量级银行截图OCR处理器部署脚本 ==="
    echo
    echo "请选择部署方式:"
    echo "1. Docker部署（推荐）"
    echo "2. Docker Compose部署（生产环境）"
    echo "3. Python本地部署"
    echo "4. 安装系统依赖"
    echo "5. 退出"
    echo
    read -p "请输入选项 [1-5]: " choice
}

# 主函数
main() {
    log_info "轻量级银行截图OCR处理器部署脚本"
    
    # 检查系统要求
    check_requirements
    
    # 创建目录和配置
    setup_directories
    setup_config
    
    while true; do
        show_menu
        
        case $choice in
            1)
                if check_docker; then
                    deploy_docker
                    show_deployment_info
                    break
                else
                    log_error "请先安装Docker"
                fi
                ;;
            2)
                if check_docker && check_docker_compose; then
                    deploy_docker_compose
                    show_deployment_info
                    break
                else
                    log_error "请先安装Docker和Docker Compose"
                fi
                ;;
            3)
                if check_python; then
                    deploy_python
                    show_deployment_info
                    break
                else
                    log_error "请先安装Python3"
                fi
                ;;
            4)
                if [[ "$OS" == "linux" ]]; then
                    if ! check_docker; then
                        install_docker_linux
                    fi
                    if ! check_docker_compose; then
                        install_docker_compose
                    fi
                    log_success "系统依赖安装完成，请重新运行脚本进行部署"
                else
                    log_warning "请手动安装Docker和Docker Compose"
                fi
                ;;
            5)
                log_info "退出部署脚本"
                exit 0
                ;;
            *)
                log_error "无效选项，请重新选择"
                ;;
        esac
    done
}

# 运行主函数
main "$@"