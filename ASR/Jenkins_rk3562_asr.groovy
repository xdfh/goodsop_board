pipeline {
    agent { label 'ubuntu-host' } // 指定在 Ubuntu 宿主机节点上运行

    parameters {
        // 参考 goodsop_demo 的参数设计，提供环境和版本选择
        // choice 的默认值是列表中的第一个元素
        choice(name: 'TARGET_ENV', choices: ['dev03', 'dev01', 'dev02'], description: '请选择要构建的目标环境')
        string(name: 'VERSION', defaultValue: 'latest', description: '镜像版本号（tag），若为 "latest" 将自动生成时间戳')
    }

    environment {
        // --- 完全参考 goodsop_demo 的环境配置 ---
        HARBOR_URL      = '192.168.1.161' // 修正 Harbor URL，不带端口
        HARBOR_PROJECT  = 'goodsop_board_asr'
        HARBOR_CREDENTIALS_ID = 'harbor-cred' // 修正为 Jenkins 中实际存在的凭据 ID
        IMAGE_NAME      = 'goodsop-asr-rk3562'
        
        // --- 应用特定配置 ---
        APP_ENV_NAME    = 'ENV_FOR_DYNACONF'
    }

    stages {
        stage('Preparation') {
            steps {
                script {
                    // --- 完全参考 goodsop_demo 的标签生成逻辑 ---
                    def imageTag = params.VERSION
                    if (imageTag == 'latest' || !imageTag.trim()) {
                        imageTag = new Date().format('yyyyMMdd_HHmmss', TimeZone.getTimeZone('Asia/Shanghai'))
                    }
                    env.IMAGE_TAG = imageTag

                    // 定义镜像全名
                    env.MAIN_IMAGE_NAME = "${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
                    env.LATEST_IMAGE_NAME = "${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest"
                    
                    echo "----------------------------------------"
                    echo "项目名称: ${IMAGE_NAME}"
                    echo "目标环境: ${params.TARGET_ENV}"
                    echo "主镜像版本: ${IMAGE_TAG}"
                    echo "最终主镜像名: ${MAIN_IMAGE_NAME}"
                    echo "最终 latest 镜像名: ${LATEST_IMAGE_NAME}"
                    echo "----------------------------------------"
                }
            }
        }
        
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "开始为 [${params.TARGET_ENV}] 环境构建 Docker 镜像 (目标平台: linux/arm64)..."
                    
                    // 定义缓存目录，使用 agent 的工作目录，确保 jenkins 用户有权限
                    def cacheDir = "/home/jenkins/agent/docker_cache/asr"
                    sh "mkdir -p ${cacheDir}"
                    
                    // 使用 docker buildx 进行跨平台构建，并添加缓存配置
                    // --cache-to: 将构建缓存导出到本地目录
                    // --cache-from: 从本地目录加载构建缓存
                    sh """
                    docker buildx build \\
                        --platform linux/arm64 \\
                        --load \\
                        -f ASR/Dockerfile \\
                        --build-arg APP_ENV=${params.TARGET_ENV} \\
                        --tag ${MAIN_IMAGE_NAME} \\
                        --cache-to type=local,dest=${cacheDir} \\
                        --cache-from type=local,src=${cacheDir} \\
                        .
                    """
                    echo "Docker 镜像构建完成。"
                }
            }
        }
        
        stage('Login to Harbor') {
            steps {
                echo "登录到 Harbor: ${HARBOR_URL}"
                withCredentials([usernamePassword(credentialsId: HARBOR_CREDENTIALS_ID, passwordVariable: 'HARBOR_PASS', usernameVariable: 'HARBOR_USER')]) {
                    sh "docker login ${env.HARBOR_URL} -u ${HARBOR_USER} -p ${HARBOR_PASS}"
                }
                echo "Harbor 登录成功。"
            }
        }

        stage('Tag and Push Images') {
            steps {
                script {
                    // --- 统一的推送逻辑 ---
                    
                    // 1. 推送主镜像
                    echo "开始推送主镜像: ${MAIN_IMAGE_NAME}"
                    sh "docker push ${MAIN_IMAGE_NAME}"
                    
                    // 2. 为主镜像打上 latest 标签并推送
                    echo "标记并推送 latest 镜像: ${LATEST_IMAGE_NAME}"
                    sh "docker tag ${MAIN_IMAGE_NAME} ${LATEST_IMAGE_NAME}"
                    sh "docker push ${LATEST_IMAGE_NAME}"
                    
                    echo "所有镜像推送完成。"
                }
            }
        }
    }
    
    post {
        always {
            script {
                // 清理本地镜像
                echo "开始清理本地镜像..."
                // 使用 || true 确保即使镜像不存在，该步骤也不会报错失败
                sh "docker rmi ${MAIN_IMAGE_NAME} || true"
                sh "docker rmi ${LATEST_IMAGE_NAME} || true"
                
                // 登出 Harbor
                echo "从 Harbor 登出..."
                sh "docker logout ${HARBOR_URL}"
                echo "清理完成。"
            }
        }
    }
}
