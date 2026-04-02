#!/bin/bash

echo "=== 本地打包 Ztailog ==="

# 构建前端
echo "构建前端..."
cd frontend
npm install
npm run build
cd ..

# 创建后端静态目录
mkdir -p backend/static
cp -rf frontend/dist/* backend/static/

# 安装 PyInstaller
pip install pyinstaller

# 打包
echo "打包 x86 版本..."
pyinstaller --onefile \
    --name ztailog_x86 \
    --add-data "backend/static:static" \
    --hidden-import uvicorn \
    --hidden-import uvicorn.loops \
    --hidden-import uvicorn.loops.auto \
    --hidden-import uvicorn.protocols \
    --hidden-import uvicorn.protocols.http \
    --hidden-import uvicorn.protocols.http.auto \
    --hidden-import uvicorn.protocols.websockets \
    --hidden-import uvicorn.protocols.websockets.auto \
    --hidden-import uvicorn.lifespan \
    --hidden-import uvicorn.lifespan.on \
    --collect-all uvicorn \
    --collect-all fastapi \
    --collect-all paramiko \
    backend/app.py

# 重命名
mv dist/app dist/ztailog_x86

echo "打包完成！"
ls -lh dist/