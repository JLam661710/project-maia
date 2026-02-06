# 🗺️ Project Maia Roadmap

## 🎯 Phase 1: Foundation & Unit Testing (✅ Completed)
**目标**: 确保每个 Agent 都是合格的独立“零件”，消除单点故障。
- [x] **Infrastructure**: 封装统一的 `LLM_Client` (API 调用、重试、错误处理)。
- [x] **Analyst Agent**: 
    - 实现 System Prompt 加载。
    - **关键**: 编写单元测试 (`tests/test_analyst.py`)，验证复杂 User Input 下的 JSON Schema 输出稳定性。
- [x] **Interviewer Agent**:
    - 实现基础对话能力。
    - 验证 `Minimal` 风格配置的实际效果。

## 🔄 Phase 2: Minimal Loop (✅ Completed)
**目标**: 跑通核心数据流，验证“分析 -> 响应”机制。
- [x] **Orchestration**: 实现 `User -> Analyst -> Interviewer` 串行流。
- [x] **State Management**: 实现 `InterviewState` 的内存流转。
- [x] **CLI Test**: 提供一个简单的命令行交互界面进行逻辑测试。

## 🎨 Phase 3: Frontend & Visuals (🚧 Current Focus)
**目标**: 实现沉浸式 Web 界面与动态 Agent 展示。
- [ ] **React Scaffold**: 初始化 React + Vite 项目，集成 p5.js。
- [ ] **Visual Migration**: 将现有 p5.js 原型移植到 React 组件中，实现 Agent 状态驱动的动画（如：Thinking 时光圈旋转）。
- [ ] **Audio Integration**: 实现“对讲机”模式的录音与播放逻辑 (ASR/TTS WebSocket)。

## 🛡️ Phase 4: Full Orchestration & Polish (全量集成)
**目标**: 引入监管与交付能力，完成系统闭环。
- [ ] **Judge Agent**: 接入审核流，拦截幻觉与不当回复。
- [ ] **Architect Agent**: 实现基于最终 State 的方案生成。
- [ ] **End-to-End Test**: 验证从语音输入到最终方案生成的完整链路。
