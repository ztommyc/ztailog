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

| 分类 | 技术 |
|------|------|
| 前端 | Vue 3.4, Element Plus, WebSocket, Vite |
| 后端 | Python 3.6+, FastAPI, WebSocket, Paramiko |
| 数据库 | SQLite |
| SSH | Paramiko |

## 🚀 快速开始

### 环境要求

- Python 3.6 或更高版本
- Node.js 16 或更高版本
- SSH 访问远程服务器权限

### 克隆仓库

```bash
git clone https://gitee.com/ztommy/ztailog.git
# 或
git clone https://github.com/ztommyc/ztailog.git
cd ztailog


### 安装后端依赖
```bash
git clone https://gitee.com/ztommy/ztailog.git
# 或
git clone https://github.com/ztommyc/ztailog.git
cd ztailog