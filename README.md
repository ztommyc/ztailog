# Ztailog - 实时日志可视化平台

基于SSH通道的在线日志查看工具，支持查看远程服务器上的文件日志、Docker日志、Podman日志和Kubernetes日志。

## 功能特点

- 🔐 安全的SSH连接管理
- 📝 实时查看文件日志（tail -f）
- 🐳 Docker容器日志实时查看
- 🐧 Podman容器日志实时查看
- ☸️ Kubernetes Pod日志实时查看
- 💾 支持完整下载文件日志
- ⚙️ 可配置初始显示行数
- 🎨 美观的Web界面
- 🔄 前后端分离，支持合并部署

## 技术栈

- 前端: Vue 3.4 + Element Plus + WebSocket
- 后端: Python 3.6 + FastAPI + WebSocket + Paramiko
- 数据库: SQLite

## 安装部署

### 开发环境

1. 克隆项目
```bash
git clone <repository-url>
cd ztailog