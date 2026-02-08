## Judge 的触发机制（Gate 逻辑：什么时候会跑）

Judge 不是每轮都跑，它在主流程里有明确的 gate，且默认每个 gate 只触发一次（通过 `judge_gate_counts` 限制）：

- 初始化：`judge_gate_counts = {"initial":0,"correction":0,"pre_completion":0,"delivery_pre_draft":0}`

核心 gate（对话中真正会“影响下一轮话术”的）：

1) **initial gate**：用户回合数 ≥ 2 且从未触发过  
   - 用途：在早期快速纠偏，把对话拉向“真实场景/证据”。
2) **pre_completion gate**：当分析状态显示“接近完成”  
   - 条件：`status` 已 Completed 或 `completion_readiness >= 80`（且未触发过）
   - 用途：作为“收口前审查”，防止过早结束。
3) **correction gate**：当用户开始聊工具/技术，但场景/损失证据不足  
   - 条件：用户回合数 ≥ 4，且最近一条用户消息命中工具关键词（cursor/trae/github/supabase/支付…），并且 `missing_info/blockers` 里包含 `Scenario Clarity` 或 `Loss Magnitude`。
