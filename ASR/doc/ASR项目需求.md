
[开发环境]
win11,进行开发和调试

[运行环境]
RK3562(debain12)，进行部署和生产使用

[项目描述]
搭建一个python框架，运行asr模型（E:\workspace\cursor\ASR\wav2vec2_quantized.tflite）

[要求]
1.模型路径和名称作为配置文件录入，代码读取使用，方便修改，配置文件注意区分环境
2.项目运行后需要提供api接口，供其他人员调用（入参为.wav或.mp3音频文件，输出转写后的文本文档）
3.采用knife4j、swagger等可用的第三方工具作为接口文档展示及接口调试工具


