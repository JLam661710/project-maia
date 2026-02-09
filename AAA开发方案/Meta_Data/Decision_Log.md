# 决策日志 (Decision Log)

## 2026-02-06: 确认 ASR 技术路径与配置
- **背景**: 在尝试集成豆包语音 2.0 (Seed-ASR) 时，遇到鉴权失败和连接断开问题。
- **决策**:
  1.  **架构模式**: 确认采用 **Backend Proxy** 模式。浏览器通过 WebSocket 发送音频到 Python 后端，后端代理转发至火山引擎。
  2.  **接口选择**: 豆包语音 2.0 (Resource ID: `volc.seedasr.sauc.duration`) **必须** 使用 `bigmodel_async` 结尾的 WebSocket 接口 (`wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async`)。
  3.  **鉴权方式**: 必须在 WebSocket Header 中显式传递 `X-Api-Resource-Id`，并使用 `AppId` + `AccessToken` 鉴权，而非 HTTP 接口的 Api-Key。
  4.  **开发策略**: 采用“独立验证环境”策略。先在 `verification_demo` 中调通协议，再移植代码到主项目。
- **状态**: ✅ 已验证 (Verified)
- **影响**: 指导了后续 `backend/services/asr_service.py` 的实现方向。

## 2026-02-06: 语音合成 (TTS) 音色确认
- **决策**: 确认使用 **云舟 2.0** 音色。
- **状态**: ✅ 已确认
- **影响**: 需在 TTS 请求参数中指定对应的 Voice Type。

## 2026-02-06: Agent 开发策略调整
- **背景**: 用户提供了经过验证的 `system_prompt_analyst.md` 和 `system_prompt_interviewer.md`。
- **决策**:
  1.  **Prompt 源**: 弃用自写 Prompt，严格使用用户提供的 System Prompt 文件。
  2.  **协作模式**: 确认 Analyst 与 Interviewer 采用 **“分析-面试”协作循环**。Analyst 负责生成 System Notice 指导 Interviewer。
- **状态**: ✅ 已执行

## 2026-02-06: 前端技术栈锁定
- **决策**: 使用 **React + Vite** 框架，配合 **p5.js** 实现“光点”视觉效果。
- **理由**: p5.js 擅长创意编程和粒子效果，符合用户对“光点”和“不复杂”的预期。
- **状态**: ✅ 已初始化

## 2026-02-06: 开发范式转型
- **决策**: 从“直接开发”转向 **“Verify first, Code later” (先验证后编码)**。
- **理由**: 避免在主项目中引入未验证的外部依赖风险。
- **状态**: ✅ 执行中

## 2026-02-09: Interviewer 单问制强约束
- **背景**: Interviewer 常出现单轮抛出 4-5 个问题，导致用户认知负担过高、回答质量下降。
- **决策**:
  1. **单问制 (强制)**: Interviewer 每次回复末尾只允许 1 个主问题。
  2. **1+1 例外 (严格限制)**: 仅允许追加 1 个“纯选择题”（点选/Yes-No/范围选项），不得追加需要组织语言的问答题。
  3. **协同链条对齐**: 同步约束 Judge 的追问建议数量（1-3 条，按优先级排序），并要求 Analyst 的 system_notice 只给出 1 个关键探索方向。
  4. **文档同步**: 将系统提示词规范同步至 `documents0/` 中的 system_prompt_* 文档，确保规范与代码一致。
- **状态**: ✅ 已执行并推送到 GitHub
