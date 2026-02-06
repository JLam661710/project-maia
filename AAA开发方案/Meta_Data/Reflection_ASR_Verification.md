# ASR 验证成功经验反思报告与 Maia 迁移方案

## 1. 成功经验总结：为什么 verification_demo 成功了？

本次对豆包语音 2.0 (Seed-ASR) 的连接与调用之所以成功，主要归功于以下几个关键策略：

### 1.1 隔离复杂性（独立验证环境）
- **做法**：我们没有直接在复杂的 Maia 后端代码中调试，而是建立了一个独立的 `verification_demo` 文件夹。
- **价值**：
  - 排除了 React 前端、AudioWorklet、复杂 WebSocket 路由等干扰因素。
  - 让我们能够专注于最核心的问题：**鉴权参数是否正确** 以及 **WebSocket 握手是否成功**。
  - 允许快速修改 `server.py` 和 `protocol.py` 进行“探测式”开发，而不用担心破坏主项目结构。

### 1.2 主动探测协议细节（Probing）
- **做法**：编写了 `probe_2_0.py` 脚本，排列组合了不同的 `Resource ID` 和 `Endpoint`。
- **价值**：
  - 官方文档可能存在滞后或模糊（例如 2.0 模型是否必须用 `_async` 接口）。
  - 通过探测，我们确切地验证了：**豆包语音 2.0 (volc.seedasr.sauc.duration) 必须配合 `bigmodel_async` 接口使用**。这是之前失败的根本原因（之前可能混用了普通接口与 2.0 资源 ID）。

### 1.3 精确的鉴权配置
- **做法**：明确区分了 HTTP 接口（使用 Api-Key）和 WebSocket 接口（使用 AppId + AccessToken）的鉴权差异。
- **价值**：
  - 修正了 `.env` 中的配置，确保了 `VOLC_APP_ID` 和 `VOLC_ACCESS_TOKEN` 被正确加载和传递。
  - 在 WebSocket Header 中正确设置了 `X-Api-Resource-Id`，这是多模型共存时的路由关键。

### 1.4 最小化全栈原型（Minimal Full-Stack Prototype）
- **做法**：`verification_demo` 虽然简单，但包含了一个完整闭环：
  - 前端：HTML + 原生 JS WebSocket（模拟真实音频流发送）。
  - 后端：FastAPI + websockets 库（作为代理转发）。
  - 协议：实现了核心的 Binary Frame 封装（Header + Payload）。
- **价值**：验证了“浏览器 -> Python 后端 -> 火山引擎”这条全链路是通畅的，证明了 Python 后端作为中间层代理的可行性。

---

## 2. 迁移方案：如何将经验应用到 Maia 正式开发？

基于上述成功经验，我们制定以下针对 Maia 主项目的开发迁移策略：

### 2.1 架构确认：保持 Python 中间层代理模式
- **决策**：Maia 将继续采用 **Browser (AudioWorklet) -> Python Backend (FastAPI) -> Volcengine (WebSocket)** 的架构。
- **理由**：
  - 浏览器端直接连接火山引擎存在 CORS 和 Header 自定义限制（尤其是需要签名的场景）。
  - Python 后端可以安全地管理 `ACCESS_TOKEN`，避免前端暴露密钥。
  - 后端可以统一处理音频格式转换（如需）和断线重连逻辑。

### 2.2 配置迁移与规范化
- **行动**：
  - 将 `verification_demo` 中验证通过的 `.env` 变量（特别是 `VOLC_ASR_ENDPOINT` 和 `VOLC_ASR_RESOURCE_ID`）正式固化到主项目的配置加载逻辑中。
  - 在 `backend/config.py` (如无则创建) 中增加对 ASR 关键参数的强校验，启动时若参数不对直接报错，避免运行时调试。

### 2.3 核心代码移植 (Porting)
我们将把 `verification_demo` 中的核心逻辑移植到 Maia 的 `backend` 模块中：

1.  **协议封装层 (`backend/utils/volc_asr_protocol.py`)**：
    - 直接复用 `verification_demo/protocol.py` 中的 `construct_audio_frame` 和 `parse_response` 函数。
    - 这些函数已经过验证，能正确处理序列化和反序列化。

2.  **服务逻辑层 (`backend/services/asr_service.py`)**：
    - 参考 `verification_demo/server.py` 的 `stream_transcription` 函数。
    - 将其封装为一个异步生成器或类（`AsrService`），接受 WebSocket 连接作为输入，输出转写后的文本流。
    - **改进点**：在正式版中，需要增加更健壮的错误处理（如火山引擎断开连接后的重试机制）和日志记录。

3.  **路由层 (`backend/routers/voice.py`)**：
    - 现有的 `voice.py` 主要处理 TTS，需要新增或合并 ASR 的 WebSocket 端点。
    - 确保路由层只负责数据转发，不包含过多的业务逻辑。

### 2.4 前端音频采集升级
- **现状**：`verification_demo` 使用了简化的音频发送逻辑。
- **迁移**：Maia 前端必须使用 `AudioWorklet` 进行音频采集（已在之前计划中）。
- **注意**：确保 `AudioWorklet` 采集到的 PCM 数据（Float32）正确转换为火山引擎要求的 16k 16bit S16LE 格式。这一点在 `verification_demo` 中是通过简单转换完成的，主项目需要保证转换的高效和准确。

### 2.5 逐步集成与测试 (Step-by-Step Integration)
不要一次性重写所有代码。建议按以下顺序进行：
1.  **Step 1**: 在 Maia 后端创建 `asr_service.py`，并在单元测试中跑通“连接火山引擎”的逻辑（不依赖前端）。
2.  **Step 2**: 在 Maia 后端开放 WebSocket 接口，使用 `verification_demo` 的前端页面（修改地址）来测试 Maia 的后端接口。
3.  **Step 3**: 才是接入 Maia 的真实 React 前端。

---

## 3. 风险预警
- **网络波动**：WebSocket 长连接对网络稳定性敏感，正式版需考虑心跳检测（Ping/Pong）。
- **并发性能**：Python `websockets` 库性能尚可，但如果用户量大，需关注 asyncio 的事件循环负载。
- **音频编码**：前端采集的采样率（通常 44.1k/48k）与 ASR 要求（16k）不一致，重采样（Resampling）算法的质量会影响识别率。

## 4. 结论
本次验证不仅打通了接口，更重要的是确立了 **“独立验证 -> 核心移植 -> 增量集成”** 的稳健开发范式。接下来的 Maia 开发将严格遵循此范式，不再进行盲目的试错式编程。
