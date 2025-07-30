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
                    try {
                        withCredentials([usernamePassword(credentialsId: HARBOR_CREDENTIALS_ID, passwordVariable: 'HARBOR_PASSWORD', usernameVariable: 'HARBOR_USERNAME')]) {
                            def harborUrl = "192.168.1.161"
                            def harborProject = "goodsop_board_asr"
                            def imageName = "${harborUrl}/${harborProject}/goodsop-asr-rk3562"
                            
                            def timestamp = new Date().format("yyyyMMdd-HHmmss")
                            def manualVersion = (params.IMAGE_VERSION ?: '').trim()
                            
                            def timestampTag = "${params.TARGET_ENV}-${timestamp}"

                            println "开始为 [${params.TARGET_ENV}] 环境构建 Docker 镜像 (目标平台: linux/arm64)..."
                            // 使用 --no-cache 禁用缓存，确保每次都获取最新变更
                            def dockerCommand = """
                                docker buildx build --platform linux/arm64 --load  \\
                                    --build-arg APP_ENV=${params.TARGET_ENV} \\
                                    -t ${imageName}:${timestampTag} \\
                                    -t ${imageName}:latest \\
                                    -f ASR/Dockerfile .
                            """

                            if (!manualVersion.isEmpty()) {
                                def manualVersionTag = "-t ${imageName}:${manualVersion}"
                                dockerCommand = dockerCommand.replace("-f ASR/Dockerfile .", "${manualVersionTag} -f ASR/Dockerfile .")
                            }
                            
                            sh dockerCommand
                            println "Docker 镜像构建完成。"

                            println "正在登录 Harbor..."
                            sh "echo ${HARBOR_PASSWORD} | docker login ${harborUrl} --username ${HARBOR_USERNAME} --password-stdin"
                            
                            println "正在推送 Docker 镜像到 Harbor..."
                            sh "docker push ${imageName}:${timestampTag}"
                            sh "docker push ${imageName}:latest"
                            if (!manualVersion.isEmpty()) {
                                sh "docker push ${imageName}:${manualVersion}"
                            }
                            println "Docker 镜像推送完成。"
                        }
                    } catch (e) {
                        currentBuild.result = 'FAILURE'
                        error "Docker 构建或推送阶段失败: ${e.toString()}"
                    } finally {
                        println "清理 Docker 登录信息..."
                        sh "docker logout 192.168.1.161"
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                // 清理工作区和镜像
                println "流水线执行完毕，开始清理..."
                cleanWs() // 清理工作区
            }
        }
    }
}
