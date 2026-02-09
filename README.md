# Project Maia 启动指南

欢迎使用 Project Maia。本项目由 Python 后端 (FastAPI) 和 React 前端 (Vite) 组成。

## 🚀 快速启动 (推荐)

我们为您准备了一键启动脚本，只需在终端运行以下命令：

```bash
./start.sh
```

该脚本会自动：
1. 检查并安装必要的依赖。
2. 启动后端服务 (8000 端口)。
3. 启动前端服务 (5173 端口)。
4. 自动打开浏览器或提示访问地址。

---

## 🛠 手动启动指南

如果您需要分别调试或了解详细步骤，请参考以下流程。

### 1. 启动后端 (Backend)

后端负责处理语音识别 (ASR) 和语音合成 (TTS) 的 WebSocket 连接。

**步骤：**

1. 打开终端，进入项目根目录：
   ```bash
   cd /Users/lishuyi/Downloads/Project_Maia
   ```

2. (可选) 创建并激活虚拟环境：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install fastapi uvicorn websockets python-dotenv
   ```

4. 启动服务：
   ```bash
   python backend/server.py
   ```
   *成功标志：终端显示 `Uvicorn running on http://0.0.0.0:8000`*

### 2. 启动前端 (Frontend)

前端提供用户交互界面。

**步骤：**

1. 打开一个新的终端窗口，进入 frontend 目录：
   ```bash
   cd /Users/lishuyi/Downloads/Project_Maia/frontend
   ```

2. 安装依赖 (仅首次需要)：
   ```bash
   npm install
   ```

3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   *成功标志：终端显示 `Local: http://localhost:5173/`*

### 3. 访问应用

打开浏览器访问：[http://localhost:5173/](http://localhost:5173/)

## 📁 常见问题

*   **端口被占用**：如果 8000 或 5173 端口被占用，请先关闭相关进程或修改配置文件。
*   **缺少依赖**：如果报错 `Module not found`，请重新运行对应的安装依赖命令 (`pip install ...` 或 `npm install`)。
*   **Python 版本**：建议使用 Python 3.8 或以上版本。
