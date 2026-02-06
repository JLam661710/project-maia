# Maia 项目：豆包大模型 1.8 参数配置指南

本文档基于 **Maia 多智能体架构** 的角色特性与 **豆包大模型 1.8 (Doubao-1.8)** 的能力，制定以下参数配置方案。

## 核心配置逻辑

所有 Agent 统一使用 **Doubao 1.8** 模型，但通过差异化的 **Thinking (推理强度)** 和 **Max Output Tokens** 来适配不同的认知任务：

*   **模型版本 (Model ID)**: `doubao-seed-1-8-251228`
*   **配置原则**:
    *   **Interviewer & Analyst**: 使用 Minimal Thinking，确保响应速度与直接性，避免过度推理导致的对话延迟或过度分析。
    *   **Judge & Summary**: 使用 Low/Medium Thinking，平衡准确性与效率。
    *   **Architect**: 使用 High Thinking，最大化利用模型的深度推理能力进行复杂架构设计。

---

## 详细参数配置表

| Agent 角色 | 模型版本 (Model ID) | Thinking (推理强度) | Max Output Tokens | Temperature | Top_p | 核心理由 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Interviewer**<br>(访谈猿) | `doubao-seed-1-8-251228` | **Minimal** | **1024** | 0.7 | 0.9 | 需保持对话流畅、响应快。短 Token 限制防止其输出长篇大论，保持“访谈”而非“演讲”的节奏。 |
| **Analyst**<br>(分析狮) | `doubao-seed-1-8-251228` | **Minimal** | **4096** | 0.1 | 0.1 | 虽然是分析角色，但在 1.8 强模型下，标准提取任务无需开启高强度推理，Minimal 模式配合 Schema 约束即可高效完成，保留较长 Token 用于输出完整 JSON。 |
| **Judge**<br>(审判鹳) | `doubao-seed-1-8-251228` | **Medium** | **2048** | 0.0 | 0.1 | 需要适度的推理来识别逻辑漏洞和伪需求，但不需要像架构设计那样深思熟虑。Medium 是最佳平衡点。 |
| **Summary**<br>(总结蜂) | `doubao-seed-1-8-251228` | **Low** | **2048** | 0.3 | 0.5 | 摘要需要一定的理解力来区分信号与噪音，Low Thinking 模式有助于提升信息提取的准确度，同时避免过度联想。 |
| **Architect**<br>(方案狸) | `doubao-seed-1-8-251228` | **High** | **8192** | 0.5 | 0.7 | 系统的“最终交付者”。开启 High Thinking 以激活最深度的逻辑规划与架构设计能力，并分配最大 Token 空间以容纳详细的 PRD 和技术蓝图。 |

> **参数说明：**
> *   **Thinking**: 对应 API 中的推理强度参数（如支持）或 Prompt 中的思维链引导强度。
>     *   *Minimal*: 直接响应，几乎无显式推理延迟。
>     *   *Low*: 简短的思维检查。
>     *   *Medium*: 标准的 CoT (Chain of Thought) 过程。
>     *   *High*: 深度、多角度的反复推演。
> *   **Max Output Tokens**: 限制模型单次输出的最大长度，防止失控并控制成本。

---

## 角色配置依据与调整说明

### 1. Interviewer (访谈猿)
*   **配置**: `Thinking=Minimal`, `Token=1024`
*   **逻辑**: 访谈猿的职责是“提问”和“引导”。开启 High Thinking 可能会导致它过度分析用户的每一句话，反而显得犹豫或啰嗦。1024 Token 足够覆盖常规对话回复（通常只需 100-300 tokens）。

### 2. Analyst (分析狮)
*   **配置**: `Thinking=Minimal`, `Token=4096`
*   **逻辑**: 这是一个显著的策略调整。原计划使用 High Thinking，但考虑到 Doubao 1.8 原生能力的提升，对于结构化提取任务，Minimal 模式能提供更快的吞吐量。4096 Token 预留了处理复杂 JSON 的空间。

### 3. Judge (审判鹳)
*   **配置**: `Thinking=Medium`, `Token=2048`
*   **逻辑**: 审判鹳需要做“价值判断”，这比单纯的信息提取更难。Medium Thinking 允许它在下结论前进行“自我辩论”，减少误判（False Positive/Negative）。

### 4. Summary (总结蜂)
*   **配置**: `Thinking=Low`, `Token=2048`
*   **逻辑**: Low Thinking 就像是给总结蜂戴了一副“聚焦眼镜”，帮助它在压缩信息时更好地识别上下文关联，防止遗漏关键细节。

### 5. Architect (方案狸)
*   **配置**: `Thinking=High`, `Token=8192`
*   **逻辑**: 方案狸是算力消耗大户。它需要生成完整的解决方案，涉及多维度权衡（技术、体验、成本）。High Thinking 是必须的，配合 8192 的 Token 上限，确保它能一次性输出详尽的文档。

## API 调用参考示例

```python
import os
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=os.environ.get("ARK_API_KEY")
)

# 示例：Architect 调用 (High Thinking)
response = client.responses.create(
    model="doubao-seed-1-8-251228",
    max_tokens=8192,
    # 假设 SDK/API 支持 reasoning_effort 参数映射 thinking 级别
    # 若不支持，需在 System Prompt 中显式要求
    # reasoning_effort="high", 
    input=[
        {"role": "system", "content": "You are the Architect..."},
        {"role": "user", "content": "Generate the PRD..."}
    ]
)
```
