# Maia 多智能体编排 (Orchestration) 设计方案

本方案定义了 Interviewer, Analyst, Judge, Summary, Architect 五个智能体如何协同工作，实现“主动响应式”访谈体验。

## 1. 核心设计理念：全同步阻塞编排 (Strict Synchronous Orchestration)

本方案采用 **“N=1 实时分析”** 与 **“全流程阻塞”** 机制，优先保证访谈的**逻辑严谨性**与**纠偏及时性**，以牺牲部分响应速度（等待时间）为代价。

*   **Analyst (分析狮)**: **逐轮运行 (Turn-by-Turn)**。用户每发送一条消息，Analyst 必须在后台完成一轮完整的分析（Context Update -> Reasoning -> State Update）。
*   **Judge (审判鹳)**: **即时介入**。在 Analyst 更新状态后，Judge 立即评估风险。
*   **Interviewer (访谈猿)**: **最后响应**。必须等待 Analyst 和 Judge 的全部工作完成后，才能获得最新的 `System Notice`，并据此生成回复。
*   **用户体验**: 用户发送消息后，输入框立即锁定，直到 Interviewer 回复完毕。期间 UI 会展示各 Agent 的工作状态（如“分析狮正在思考...”、“审判鹳正在评估...”），提供透明的可解释性。

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
2.  Interviewer 发送开场白（或响应用户第一句）。
3.  **首轮即分析**：从用户的第一句回复开始，Analyst 立即介入。

### 3.2 交互循环 (Interaction Loop)

设定批处理阈值 **N = 1**。

#### 标准同步处理链 (Standard Sync Chain)

当用户点击“发送”按钮：

1.  **锁定输入 (Input Lock)**: 
    *   前端立即禁用输入框。
    *   显示状态：“Interviewer 正在接收...”

2.  **Analyst 分析 (Analyst Step)**:
    *   **触发**: 收到用户最新消息。
    *   **动作**: Analyst 读取 `compressed_memory` + `recent_messages` (含最新句) + `previous_state`。
    *   **UI 状态**: 显示“分析狮正在提取关键信息...”
    *   **输出**: 更新 `InterviewState`。

3.  **Judge 评估 (Judge Step)**:
    *   **触发**: Analyst 更新完毕。
    *   **动作**: Judge 检查 `InterviewState` 是否存在幻觉风险、逻辑矛盾或需要强制干预。
    *   **UI 状态**: 显示“审判鹳正在评估...” (若无风险可快速闪过)。
    *   **输出**: 生成 `system_notice` (纠偏指令或下一步指引)。

4.  **Interviewer 响应 (Interviewer Step)**:
    *   **触发**: Judge 评估完毕。
    *   **动作**: 读取最新的 `InterviewState` 和 `system_notice`，生成回复。
    *   **UI 状态**: 显示“访谈猿正在回复...”
    *   **输出**: Stream 回复文本给用户。

5.  **解锁输入 (Unlock)**:
    *   Interviewer 回复完毕。
    *   **Summary 检查**: 若触发 Summary (Token > 阈值)，则继续保持锁定并运行 Summary，完成后再解锁。
    *   恢复输入框。

### 3.3 交付与迭代 (Delivery & Iteration)

当 Analyst 判定 `status: "Completed"` 且 Judge 批准后：

1.  **Architect 生成**: 系统调用 Architect 生成方案（DOC_01 ~ DOC_06）。
2.  **循环迭代**:
    *   用户阅读方案。
    *   若不满意，用户可在对话框继续提出修改意见。
    *   系统进入新一轮同步循环：Interviewer 接收 -> Analyst 更新 -> Architect 重新生成。

---

## 4. 方案权衡：为什么选择全同步？

*   **质量优先**: 每一句回复都经过了 Analyst 的深思熟虑和 Judge 的严格审查，确保 Interviewer 绝不跑偏。
*   **消除幻觉**: Judge 的实时拦截能力最大化，能在幻觉产生的第一时间掐灭。
*   **体验代价**: 用户等待时长显著增加（预计每轮 15-20秒+）。
*   **缓解策略**: 通过前端 UI 的**过程透明化**（展示各 Agent 忙碌状态），缓解用户的等待焦虑，将其转化为“系统正在认真工作”的信任感。

---

## 5. 异常处理

### 5.1 响应超时
*   若 Analyst 或 Judge 运行超过 30秒，前端应提示“思考时间较长，请稍候...”。
*   若超过 60秒，强制跳过当前步骤，降级为 Interviewer 直接回复（Fail-safe），并在后台记录错误日志。

### 5.2 Summary 冲突
*   由于是全同步串行流程，Summary 不会与 Analyst 发生冲突。Summary 仅在 Interviewer 回复完成后、用户解锁前运行。

---

## 6. 伪代码实现 (Pythonic Pseudocode)

```python
class MaiaOrchestrator:
    def __init__(self):
        self.state = InterviewState()
        self.context = SystemContext()

    async def chat(self, user_input):
        # 1. Lock UI & Update History
        self.ui.lock_input()
        self.context.recent_messages.append(UserMessage(user_input))

        try:
            # 2. Analyst Run (Blocking)
            self.ui.set_status("Analyst Working...")
            new_state = await self.agents.analyst.analyze(
                summary=self.context.compressed_memory,
                recent_messages=self.context.recent_messages, 
                previous_state=self.state
            )
            self.state = new_state

            # 3. Judge Run (Blocking)
            self.ui.set_status("Judge Reviewing...")
            judgment = await self.agents.judge.evaluate(new_state)
            self.context.system_notice = judgment.instruction

            # 4. Check Completion
            if self.state.status == "Completed" and judgment.approved:
                 await self.trigger_architect()
                 return # End flow or continue

            # 5. Interviewer Reply (Blocking)
            self.ui.set_status("Interviewer Replying...")
            response = await self.agents.interviewer.run(self.context)
            self.context.recent_messages.append(AssistantMessage(response))
            yield response 

            # 6. Summary Run (Blocking if needed)
            if self.should_compress():
                self.ui.set_status("Summary Compressing...")
                self.context.compressed_memory = await self.agents.summary.compress(...)
                self.context.recent_messages = self.truncate(...)

        except Exception as e:
            self.ui.show_error(str(e))
            # Fail-safe reply
            yield "抱歉，系统处理超时，请重试。"
        
        finally:
            # 7. Unlock UI
            self.ui.unlock_input()
            self.ui.clear_status()
```
