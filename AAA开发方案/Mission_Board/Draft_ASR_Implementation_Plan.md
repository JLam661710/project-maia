# Maia 语音识别 (ASR) 功能开发实施方案 (草稿)

> **⚠️ 核心原则**: 
> 1. **严格调研**: 基于官方文档与协议规范，不臆想。
> 2. **前后端分离**: 前端负责采集与降采样，后端负责协议代理与鉴权。
> 3. **实时反馈**: 采用流式（Streaming）方案，确保“说话即出字”。

## 1. 技术背景与协议分析

### 1.1 接口定义
- **服务地址**: `wss://openspeech.bytedance.com/api/v3/sauc/bigmodel` (豆包大模型双向流式)
- **鉴权方式**: 
  - HTTP Header 鉴权 (握手阶段): `X-Api-App-Key`, `X-Api-Access-Key`, `X-Api-Resource-Id`
- **协议格式**: 火山引擎 V3 二进制协议 (与 TTS 共用同一套底层封包逻辑)。

### 1.2 数据流向
1. **上行 (Audio)**:
   - 麦克风采集 (48kHz/44.1kHz, Float32) -> 前端重采样 (16kHz) -> 转换 (Int16 PCM) -> WebSocket -> 后端 -> 火山引擎。
2. **下行 (Text)**:
   - 火山引擎 -> 识别结果 (JSON) -> 后端 -> WebSocket -> 前端展示。

### 1.3 关键约束
- **音频格式**: 必须为 **16kHz, 16bit, Mono (单声道)** PCM。
- **包大小**: 建议每包 **100ms - 200ms** (约 3200 - 6400 字节)。
- **压缩**: 为了简化开发，客户端请求时 `Compression` 字段设为 `0` (无压缩)，服务端也会返回无压缩数据。

---

## 2. 后端开发规划 (FastAPI)

### 2.1 协议层升级 (`backend/utils/volc_tts_protocol.py`)
*现状*: 现有的 `protocols.py` (即 `volc_tts_protocol.py`) 是通用的。
*确认*: 
- 检查 `MsgType.AudioOnlyClient` (0b0010) 是否存在 ✅。
- 检查 `MsgTypeFlagBits.LastNoSeq` (0b0010) 是否存在 ✅ (用于发送结束包)。
- 结论：无需修改协议层代码，直接复用。

### 2.2 服务层 (`backend/services/asr_service.py`)
- **类设计**: `VolcASRService`
- **核心方法**:
  ```python
  async def stream_asr(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
      # 1. 连接火山引擎
      # 2. 发送 FullClientRequest (配置 format=raw, rate=16000, language=zh-CN)
      # 3. 并发任务:
      #    - Task A: 循环读取 audio_generator，封装为 AudioOnlyClient 消息发送。
      #      (注意：收到前端的“结束”信号时，发送带 LastNoSeq 标志的空包)
      #    - Task B: 循环接收服务端消息，解析 JSON，yield 文本结果。
  ```

### 2.3 接口层 (`backend/routers/voice.py`)
- **新增路由**: `/ws/asr`
- **逻辑**:
  - 建立 WebSocket 连接。
  - 启动双向转发：
    - 接收前端 binary (PCM) -> 喂给 `stream_asr`。
    - 接收 `stream_asr` 的文本 -> 发送 text/json 给前端。

---

## 3. 前端开发规划 (React)

### 3.1 音频录制器 (`frontend/src/utils/audioRecorder.js`)
*这是前端最复杂的部分，不能直接用 `MediaRecorder` (它通常输出 WebM/Ogg)，必须用 `AudioContext` 获取原始 PCM。*

- **核心逻辑**:
  1. `navigator.mediaDevices.getUserMedia({ audio: true })`
  2. `audioContext.createMediaStreamSource(stream)`
  3. `ScriptProcessorNode` 或 `AudioWorklet` (推荐 Worklet，但 ScriptProcessor 兼容性更好且代码简单，暂选 ScriptProcessor)。
  4. **重采样 (Resample)**: 浏览器默认 48kHz/44.1kHz -> 目标 16kHz。
     - *算法*: 简单的线性插值或降采样算法。
  5. **位深转换**: Float32 (-1.0 ~ 1.0) -> Int16 (-32768 ~ 32767)。

### 3.2 交互逻辑 (`App.jsx`)
- **状态管理**: `isRecording` (bool), `asrResult` (string)。
- **操作**:
  - **点击按钮 (Start)**: 初始化 WebSocket -> 初始化 Recorder -> 开始推流。
  - **再次点击 (Stop)**: 停止 Recorder -> 发送 WebSocket 结束帧 -> 等待最终结果 -> 关闭连接。
- **显示**:
  - 实时显示流式结果 (当前句子的变动)。
  - 最终显示完整文本。

---

## 4. 实施步骤

1.  **后端服务**: 创建 `backend/services/asr_service.py`，实现 ASR 代理逻辑。
2.  **后端路由**: 在 `backend/routers/voice.py` 增加 `/ws/asr`。
3.  **前端工具**: 创建 `frontend/src/utils/audioRecorder.js` (含重采样逻辑)。
4.  **前端集成**: 修改 `App.jsx`，增加录音按钮和文本展示区域。
5.  **联调**: 验证 48k->16k 重采样音质，验证实时识别准确率。

## 5. 风险预案
- **采样率不匹配**: 如果重采样算法写错，识别出来的声音会变调（像快放或慢放），导致识别乱码。
  - *对策*: 先录制一段 PCM 下来到本地播放验证，确认音调正常再接 ASR。
- **VAD (静音检测)**: 豆包大模型支持服务端 VAD，我们不需要在前端做复杂的静音检测，手动点击停止即可。
