#!/bin/bash

# 确保脚本在发生错误时退出
set -e

echo "开始部署 Text2SQL 项目..."

# 拉取最新代码（如果是从git部署的话）
# git pull origin main

# 构建并启动服务
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 下载必要的模型
echo "下载 Ollama 模型..."
docker-compose exec ollama ollama pull qwen2.5-coder:latest
docker-compose exec ollama ollama pull bge-large:latest

echo "部署完成！"
echo "服务访问地址: http://localhost:5000" 