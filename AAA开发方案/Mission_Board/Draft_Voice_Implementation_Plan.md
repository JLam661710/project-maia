# Maia 语音功能开发实施方案 (草稿)

> **⚠️ 原则强调**: 
> 1. 分阶段开发：先攻克 TTS (语音合成)，再处理 ASR (语音识别)。
> 2. 严谨准备：完全吃透协议与文档后再编码。
> 3. 架构分离：前端负责播放/录音，后端负责协议代理/流转。

## 第一阶段：流式语音合成 (TTS)

### 1. 技术背景与协议分析
基于 `/Users/lishuyi/Downloads/Project_Maia/单向流式语音合成 api 接口及测试` 中的文档与示例代码：
- **协议**: WebSocket 二进制协议 (非纯文本 JSON)。
- **鉴权**: 需要 `X-Api-App-Key` (AppID) 和 `X-Api-Access-Key` (Token)。
- **核心流程**: 建立连接 -> 发送 FullClientRequest (包含文本) -> 接收 AudioOnlyServer (音频数据) -> 接收 FullServerResponse (结束信号)。
- **数据格式**: 需要复用 `protocols.py` 中的 `Message` 类进行二进制封包/解包。

### 2. 后端开发规划 (FastAPI)

#### 2.1 协议层 (`backend/utils/volc_tts_protocol.py`)
- **任务**: 将示例代码中的 `protocols.py` 移植到项目中。
- **目的**: 处理复杂的二进制头部、版本位、消息类型等底层逻辑，确保与火山引擎服务的通信协议严格一致。

#### 2.2 服务层 (`backend/services/tts_service.py`)
- **类设计**: `VolcTTSService`
- **核心方法**: 
  ```python
  async def stream_tts(self, text: str) -> AsyncGenerator[bytes, None]:
      # 1. 建立到火山引擎的 WebSocket 连接
      # 2. 发送合成请求 (携带 Token 和 Voice Type)
      # 3. 循环接收音频数据包 (AudioOnlyServer)
      # 4. yield 音频二进制数据
      # 5. 检测到 SessionFinished 时关闭连接
  ```
- **配置**: 读取 `.env` 中的 `VOLC_APP_ID`, `VOLC_ACCESS_TOKEN`, `VOLC_TTS_VOICE_TYPE`。

#### 2.3 接口层 (`backend/main.py` 或 `backend/routers/voice.py`)
- **新增 WebSocket 路由**: `/ws/tts`
- **逻辑**:
  1. 前端建立连接。
  2. 前端发送待合成文本 (或由后端 Interviewer 产生文本时主动推送)。
  3. 后端调用 `VolcTTSService`。
  4. 后端将收到的音频 chunk 实时转发给前端。

### 3. 前端开发规划 (React + p5.js)

#### 3.1 音频播放器 (`frontend/src/utils/audioStreamPlayer.js`)
- **方案**: 使用 `AudioContext` 进行流式播放。
- **机制**: 
  - 收到 WebSocket 的二进制 PCM 数据 (ArrayBuffer) -> Int16 转 Float32 -> 直接播放。
  - 使用时间轴调度，保证多个音频片段连续播放。
- **视觉联动**: 使用 `AnalyserNode` 获取音量/频谱，实时驱动 `MaiaCanvas` 的光点呼吸频率/大小。

### 4. 实施步骤

1. **协议移植**: 复制并清理 `protocols.py` 代码。
2. **后端打通**: 编写单元测试 `tests/test_tts_service.py`，验证能否生成音频文件。
3. **前端播放**: 实现简单的 AudioContext 播放器，验证能否播放后端传来的二进制流。
4. **视觉绑定**: 将音频振幅映射到光点动画参数。

---

## 试用步骤（小白版）
1. 打开终端（Terminal），进入项目根目录：`/Users/lishuyi/Downloads/Project_Maia`。
2. 启动后端：
   - 执行：`python -m backend.server`
   - 看到 “Uvicorn running on http://0.0.0.0:8000” 就是成功。
3. 另开一个终端，启动前端：
   - 进入前端目录：`cd frontend`
   - 执行：`npm run dev`
   - 看到 `http://localhost:5173/` 就是成功。
4. 打开浏览器访问 `http://localhost:5173/`。
5. 在页面上任意位置点击一下，Maia 会说话，光点会跟着声音呼吸。

## 第二阶段：流式语音识别 (ASR) [待定]
*注：待 TTS 功能完全稳定并验收后，再启动此阶段设计。*

## 风险评估与应对
- **网络延迟**: 使用 WebSocket 全双工流式传输，最大限度降低首字延迟。
- **音频格式**: 默认使用 PCM 或 WAV，前端 AudioContext 解码兼容性好。
- **鉴权失败**: 严格检查 `.env` 配置，开发前先用 curl 或简单脚本验证 Token 有效性。
