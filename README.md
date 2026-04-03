# Ztailog - 实时日志可视化平台

[![Gitee](https://img.shields.io/badge/Gitee-ztailog-red?logo=gitee)](https://gitee.com/ztommy/ztailog.git)
[![GitHub](https://img.shields.io/badge/GitHub-ztailog-black?logo=github)](https://github.com/ztommyc/ztailog.git)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.4-brightgreen.svg)](https://vuejs.org/)

## 📖 简介

Ztailog 是一个基于 Web 的实时日志可视化平台，通过 SSH 通道查看远程服务器上的日志。支持实时查看文件日志、Docker 容器日志、Podman 容器日志和 Kubernetes Pod 日志。

## ✨ 功能特点

- 🔐 **安全 SSH 连接**：通过密码或私钥认证连接远程服务器
- 📝 **实时文件日志**：使用 `tail -f` 命令监控文件日志
- 🐳 **Docker 日志**：实时查看 Docker 容器日志（自动排除 k8s 容器）
- 🐧 **Podman 日志**：实时查看 Podman 容器日志
- ☸️ **Kubernetes 日志**：支持命名空间的 K8s Pod 日志实时查看
- 💾 **日志下载**：下载完整文件或当前查看的日志（大文件自动压缩）
- 📜 **日志历史**：自动保存文件日志路径，带使用统计
- 🎨 **语法高亮**：关键词颜色标记（错误、警告、成功、信息、调试）
- 🔄 **自动滚动**：新日志到达时自动滚动到底部
- 📱 **响应式设计**：支持桌面和移动设备
- 🖱️ **可调整侧边栏**：拖拽调整侧边栏宽度
- 💾 **SQLite 数据库**：轻量级本地数据库存储配置

## 🛠 技术栈

| 分类  | 技术                                        |
| --- | ----------------------------------------- |
| 前端  | Vue 3.4, Element Plus, WebSocket, Vite    |
| 后端  | Python 3.6+, FastAPI, WebSocket, Paramiko |
| 数据库 | SQLite                                    |
| SSH | Paramiko                                  |

## 🚀 快速开始

### 环境要求

- Python 3.6 或更高版本
- Node.js 16 或更高版本
- SSH 访问远程服务器权限

### 克隆仓库

```bash
git clone https://github.com/ztommyc/ztailog.git
cd ztailog
# 或
git clone https://github.com/ztommyc/ztailog.git
cd ztailog
```

### 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

如果遇到安装问题，请使用以下命令：

```bash
# 升级 pip
python3 -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install -r requirements.txt -i http://mirrors.cloud.aliyuncs.com/pypi/simple/ --trusted-host mirrors.cloud.aliyuncs.com
```

### 安装前端依赖

```bash
cd frontend

# 安装 Node.js 依赖
npm install

# 如果安装速度慢，使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 或使用淘宝镜像
npm install --registry=https://registry.npm.taobao.org
```

### 构建前端

```bash
npm run build

# 复制构建文件到后端静态目录
mkdir -p ../backend/static
cp -rf dist/* ../backend/static/
```

### 运行应用

```bash
cd ../backend
python app.py
```

访问应用：`http://localhost:60501`

## 📦 部署方式

### 开发模式运行

```bash
# 终端1 - 后端
cd backend
python app.py

# 终端2 - 前端（开发模式）
cd frontend
npm run dev
```

访问：`http://localhost:60500`

### 生产部署

```bash
# 一键构建前后端
python build.py

# 进入部署目录
cd dist

# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

### 打包为单可执行文件

#### 安装 PyInstaller

```bash
pip install pyinstaller
```

#### 打包 x86 版本

```bash
# 先构建前端
cd frontend
npm run build
cd ..

# 打包
pyinstaller --onefile \
    --name ztailog_x86 \
    --add-data "frontend/dist:static" \
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
    backend/app.py
```

#### 运行打包后的文件

```bash
# 直接运行
./dist/ztailog_x86

# 指定端口（修改 app.py 中的端口配置）
PORT=8080 ./dist/ztailog_x86
```

### Docker 部署

创建 `Dockerfile`：

```bash
FROM python:3.9-slim

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 复制前端构建文件
COPY frontend/dist ./static

EXPOSE 60501

CMD ["python", "app.py"]
```

### systemd 服务配置（Linux）

创建 `/etc/systemd/system/ztailog.service`：

```bash
[Unit]
Description=Ztailog Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ztailog
ExecStart=/usr/bin/python3 /opt/ztailog/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ztailog
sudo systemctl start ztailog
sudo systemctl status ztailog
```

### Nginx 反向代理（可选）

```bash
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:60501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ⚙️ 配置说明

### 默认端口

| 服务                 | 端口    |
| ------------------ | ----- |
| 后端 API & WebSocket | 60501 |
| 前端（开发模式）           | 60500 |

### SSH 主机配置

通过 Web 界面添加 SSH 主机：

| 字段   | 说明             |
| ---- | -------------- |
| 主机名称 | 服务器别名          |
| 主机地址 | IP 地址或主机名      |
| 端口   | SSH 端口（默认 22）  |
| 用户名  | SSH 用户名        |
| 密码   | 密码（与私钥二选一）     |
| 私钥   | RSA 私钥（与密码二选一） |

### 日志配置

| 配置项    | 说明      | 默认值 |
| ------ | ------- | --- |
| 默认显示行数 | 初始显示的行数 | 100 |
| 自动滚动   | 自动滚动到底部 | 开启  |
| 语法高亮   | 关键词颜色标记 | 开启  |

## 📖 使用指南

### 查看文件日志

1. 从左侧边栏选择主机

2. 选择"文件日志"

3. 输入日志文件路径（如：`/var/log/messages`）

4. 点击"开始"查看实时日志

5. 使用"下载"按钮保存完整文件或当前日志

### 查看 Docker 日志

1. 选择主机

2. 选择"Docker 日志"

3. 从下拉框选择容器（自动排除 k8s 容器）

4. 点击"开始"查看实时日志

### 查看 Podman 日志

1. 选择主机

2. 选择"Podman 日志"

3. 选择容器

4. 点击"开始"查看日志

### 查看 Kubernetes 日志

1. 选择主机

2. 选择"K8s 日志"

3. 选择命名空间和 Pod

4. 点击"开始"查看日志

## 🔧 API 接口

### 主机管理

| 方法     | 端点                | 说明          |
| ------ | ----------------- | ----------- |
| GET    | `/api/hosts`      | 获取所有 SSH 主机 |
| POST   | `/api/hosts`      | 添加 SSH 主机   |
| GET    | `/api/hosts/{id}` | 获取主机详情      |
| PUT    | `/api/hosts/{id}` | 更新主机        |
| DELETE | `/api/hosts/{id}` | 删除主机        |

### 日志操作

| 方法     | 端点                                        | 说明       |
| ------ | ----------------------------------------- | -------- |
| GET    | `/api/hosts/{id}/log-config`              | 获取日志配置   |
| PUT    | `/api/hosts/{id}/log-config/{type}`       | 更新日志配置   |
| GET    | `/api/hosts/{id}/containers/{type}`       | 获取容器列表   |
| GET    | `/api/hosts/{id}/download`                | 下载日志文件   |
| GET    | `/api/hosts/{id}/log-history`             | 获取日志路径历史 |
| POST   | `/api/hosts/{id}/log-history`             | 保存日志路径   |
| DELETE | `/api/hosts/{id}/log-history/{historyId}` | 删除历史     |

### WebSocket

| 端点                                       | 说明    |
| ---------------------------------------- | ----- |
| `ws://localhost:60501/ws/logs/{host_id}` | 实时日志流 |

## 📁 项目结构

```
ztailog/
├── backend/
│   ├── app.py              # FastAPI 主应用
│   ├── database.py         # SQLite 数据库模型
│   ├── ssh_manager.py      # SSH 连接管理
│   ├── log_handlers.py     # 日志流处理器
│   ├── requirements.txt    # Python 依赖
│   └── static/             # 构建后的前端文件
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HostManager.vue
│   │   │   └── LogViewer.vue
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── build.py                # 构建脚本
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
└── README.md
```

## 🐛 故障排除

### Docker 容器不显示

```bash
# 确保 Docker 正在运行
systemctl status docker

# 检查 SSH 用户权限
ssh user@host "docker ps -a"

# 手动测试命令
docker ps -a --format '{{.Names}}|{{.ID}}|{{.Status}}|{{.Image}}'
```

### 日志不显示

```bash
# 检查文件是否存在且可读
ssh user@host "test -f /var/log/messages && echo 'exists'"

# 测试 tail 命令
ssh user@host "tail -10 /var/log/messages"

# 查看后端日志
tail -f backend/ztailog.log
```

# 

### WebSocket 连接失败

```bash
# 检查端口是否开放

netstat -tlnp | grep 60501

# 检查防火墙

firewall-cmd --list-ports
iptables -L -n | grep 60501

# 开放端口（如有需要）

firewall-cmd --add-port=60501/tcp --permanent
firewall-cmd --reload
```

### 打包后前端不显示

```bash
检查前端是否构建

ls -la frontend/dist/

# 检查静态文件是否复制

ls -la backend/static/

# 查看运行时输出

./dist/ztailog_x86 2>&1 | grep -i static
```

# 

### pip 安装失败

```bash
升级 pip

python3 -m pip install --upgrade pip

# 使用国内镜像

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 单独安装问题包

pip install greenlet==2.0.2 --no-binary=greenlet
```

# 

### npm install 失败

```bash
# 清理缓存

npm cache clean --force

# 删除 node_modules 重新安装

rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmmirror.com

# 使用 cnpm

npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

# 

## 🔒 安全建议

- 🔑 优先使用私钥认证而非密码

- 🔒 生产环境使用 HTTPS

- 🔄 定期更新 SSH 凭证

- 👤 限制 SSH 用户权限为只读

- 🛡️ 使用防火墙限制 60501 端口访问

- 📝 保持应用和依赖更新

- 🔐 不要在代码中硬编码密码

- 📁 定期备份 SQLite 数据库

## 📊 性能优化

- 对于大文件，调整默认显示行数（10-1000）

- 使用自动滚动持续监控

- 下载日志进行离线分析

- 清理不用的 SSH 主机配置

- 定期清理日志历史记录（超过1000条）

- 使用 Nginx 缓存静态资源

## 🤝 贡献

欢迎贡献代码！请提交 Pull Request。

1. Fork 本仓库

2. 创建特性分支：`git checkout -b feature/AmazingFeature`

3. 提交更改：`git commit -m 'Add some AmazingFeature'`

4. 推送分支：`git push origin feature/AmazingFeature`

5. 提交 Pull Request

### 

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](https://license/) 文件

## 📧 联系方式

- Gitee: https://gitee.com/ztommy/ztailog.git

- GitHub: https://github.com/ztommyc/ztailog.git

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架

- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架

- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库

- [Paramiko](https://www.paramiko.org/) - SSHv2 协议库

- [highlight.js](https://highlightjs.org/) - 代码语法高亮

---

⭐ 如果这个项目对你有帮助，请给个 Star！