# Maia 多智能体编排 (Orchestration) 设计方案

本方案定义了 Interviewer, Analyst, Judge, Summary, Architect 五个智能体如何协同工作，实现“主动响应式”访谈体验。

## 1. 核心设计理念：响应优先异步编排 (Response-First Async Orchestration)

本方案采用 **“响应优先 (Response-First)”** 与 **“后台异步分析 (Async Background)”** 机制，旨在**最大化用户交互流畅度**，同时保持后台强大的逻辑分析能力。

*   **Interviewer (访谈猿)**: **立即响应**。在收到用户输入后，基于上一轮的系统指令（System Notice）和当前输入，**立即**生成回复，不等待后台分析。这确保了类似真人的“秒回”体验。
*   **Analyst (分析狮)**: **后台异步 (Background Async)**。在 Interviewer 回复的同时，Analyst 在后台启动深度分析。
*   **Judge (审判鹳)**: **按需介入 (Conditional)**。在 Analyst 分析完成后，若发现风险或关键节点，Judge 介入评估并生成修正指令（System Notice），供 Interviewer **下一轮**使用。
*   **用户体验**: 用户发送消息 -> Interviewer 立即回复 -> 用户阅读/思考/输入的同时 -> 后台 Analyst/Judge 完成思考 -> 下一轮循环。**几乎零等待**。

---

## 2. 状态定义 (State Definitions)

系统维护两个核心状态对象，在 Agents 之间流转：

### 2.1 `InterviewState` (JSON)
由 **Analyst** 维护的结构化真理源。
*   **可视化要求**：在开发阶段，该 JSON State 需在 UI 右侧（或调试面板）**实时展示**，保持透明可解释。

```json
{
  "session_id": "uuid",
  "processed_turns": 12, // 已处理的对话轮次
  "status": "Profiling" | "DeepDive" | "Solutioning" | "Completed",
  "user_profile": { ... },
  "pain_points": [ ... ],
  "constraints": { ... },
  "completeness_score": 65,
  "last_updated": "timestamp"
}
```

### 2.2 `SystemContext` (Runtime Object)
运行时上下文，用于控制当前轮次的生成。

```json
{
  "recent_messages": [...], // 未被压缩的最近 N 轮对话
  "compressed_memory": "String (Summary)", // 总结蜂压缩后的长期记忆
  "latest_state": "Object (InterviewState)", // 最新的分析状态
  "system_notice": "String", // 审判鹳/分析狮给访谈猿的下一句指令
  "blocking_agent": "None" | "Analyst" | "Judge" | "Summary" // 当前谁正在阻塞系统
}
```

---

## 3. 详细编排流程 (Orchestration Flow)

### 3.1 启动阶段 (Initialization)
1.  系统初始化 `InterviewState` 为空。
2.  Analyst 生成初始 `System Notice`。
3.  Interviewer 发送开场白。
4.  进入主循环，等待用户输入。

### 3.2 交互循环 (Interaction Loop)

当用户输入消息（User Input）：

1.  **Interviewer 立即响应 (Immediate Reply)**:
    *   **触发**: 收到 User Input。
    *   **动作**: 结合 User Input 和当前的 `System Notice`，立即生成回复。
    *   **UI**: 立即显示回复。

2.  **并行处理 (Parallel Processing)**:
    *   **前台**: 解锁输入框，允许用户阅读并输入下一句。
    *   **后台**: 启动 Analyst + Judge 任务链。

3.  **后台分析 (Background Analysis)**:
    *   **Analyst**: 基于最新对话更新 `InterviewState`。
    *   **Judge (Conditional)**: 若 Analyst 标记风险或状态变更，Judge 介入，更新 `System Notice`（用于修正下一轮 Interviewer 的行为）。
    *   **Summary (Conditional)**: 每 N 轮压缩一次历史记录。

4.  **同步栅栏 (Sync Barrier)**:
    *   当用户提交**下一句**输入时，系统确保后台任务已完成（通常用户输入的时间远长于后台分析时间）。
    *   如果后台还在跑，UI 会短暂显示“正在同步思维...”，确保数据一致性。

### 3.3 交付与迭代 (Delivery & Iteration)

当 Analyst 判定 `status: "Completed"` 且 Judge 批准后：

1.  **Architect 生成**: 系统调用 Architect 生成方案（DOC_01 ~ DOC_06）。
2.  **循环迭代**:
    *   用户阅读方案。
    *   若不满意，用户可在对话框继续提出修改意见。
    *   系统进入新一轮循环。

---

## 4. 方案权衡：为什么选择响应优先？

*   **体验优先**: 模仿人类对话的节奏——“先回应，再深思”。
*   **掩盖延迟**: 利用用户阅读回复和思考下一句的时间（通常 10-30秒），在后台完成耗时的分析工作。
*   **自我修正**: 如果 Interviewer 说错了，Judge 会在后台发现，并在下一轮通过 `System Notice` 指示 Interviewer 进行纠正（“刚才我可能理解偏了...”），这比长时间阻塞等待更符合自然对话习惯。

---

## 5. 异常处理

### 5.1 响应超时
*   **前台超时**: Interviewer 响应应在 1-3秒内开始 Stream。
*   **后台超时**: Analyst/Judge 运行若超过 30秒，不影响当前对话，但会阻塞**下一轮**对话的开始（同步栅栏机制）。此时前端显示“系统正在深度思考...”。

### 5.2 状态一致性 (Race Conditions)
*   **栅栏机制 (Barrier)**: 必须确保上一轮的后台任务（Analyst/Judge）全部完成后，才能处理下一轮的 `User Input`。这是为了保证 Analyst 拿到的是完整的历史上下文，避免状态错乱。

---

## 6. 伪代码实现 (Pythonic Pseudocode)

```python
class MaiaOrchestrator:
    async def chat_loop(self):
        # Initial Setup
        state = await self.analyst.init_state()
        system_notice = state.notice
        
        while True:
            # 1. Wait for User Input
            user_input = await self.get_user_input() 
            
            # 2. Interviewer Responds IMMEDIATELY (The Mouth)
            # Uses current system_notice (from previous turn)
            reply = await self.interviewer.generate(user_input, system_notice)
            yield reply
            
            # 3. Parallel Execution: Unlock Input vs Background Analysis
            # Task A: Wait for NEXT user input (User reading/typing)
            input_task = asyncio.create_task(self.get_next_input())
            
            # Task B: Run Analysis (The Brain)
            analysis_task = asyncio.create_task(self.run_background_analysis(user_input, state))
            
            # 4. Sync Barrier
            # We need the analysis to finish before we process the NEXT input
            # But we want to let the user TYPE while analysis is running
            
            next_user_input = await input_task
            new_state, judge_report = await analysis_task
            
            # 5. Update State for NEXT turn
            state = new_state
            if judge_report:
                system_notice = judge_report.instruction
            
            user_input = next_user_input
```

---

## 7. 语音集成兼容性 (Voice Integration Compatibility)

本架构设计（Response-First Async）与语音交互（ASR/TTS）**天然兼容**，且能最大化利用语音播报的时间窗口。

### 7.1 兼容性分析

| 模块 | 文本模式 (Current) | 语音模式 (Future) | 兼容性结论 |
| :--- | :--- | :--- | :--- |
| **输入 (Input)** | `readline` (阻塞等待回车) | `ASR Stream` (VAD检测到静音后提交) | **兼容**。ASR 最终输出的 `Final Result` 即为 `user_input`。 |
| **输出 (Output)** | `print` (文本显示) | `TTS Engine` (语音合成与播放) | **兼容**。Interviewer 的文本直接送入 TTS。 |
| **延迟 (Latency)** | 用户阅读文本的时间 | TTS 语音播报的时间 (通常更长) | **完美匹配**。语音播报时间正好用于掩盖后台 Analyst 的分析延迟。 |
| **打断 (Interrupt)** | 用户输入新消息 | 用户说话打断 TTS | **兼容**。打断视为新的 Input，取消当前播放，进入新循环。 |

### 7.2 架构映射

*   **耳朵 (Ear)**: ASR 模块。替代 `input()`。监听用户语音，转为 Text。
*   **嘴巴 (Mouth)**: Interviewer + TTS。Interviewer 生成文本，TTS 读出来。
*   **大脑 (Brain)**: Analyst + Judge。在“嘴巴”说话的时候，大脑在后台疯狂转动。

### 7.3 结论
当前的 **“响应优先 + 异步后台”** 架构不仅支持语音，而且是**语音交互的最佳实践架构**。它利用了 TTS 播报的自然延时（Cover Latency），让用户感觉不到后台复杂的推理过程，实现了“像人一样边说边想”的效果。
