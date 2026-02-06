import logging
import json
from typing import Dict, List, Optional, Any

from utils.llm_client import LLMClient
from prompts.analyst_prompt import ANALYST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# 定义初始空状态，确保结构完整
INITIAL_STATE = {
  "schema_version": "v2.1-cognitive",
  "status": "In Progress",
  "completion_readiness": 0,
  "blockers": [],
  "missing_info": ["ALL"],
  "interview_session": {
    "stage": "initial",
    "status": "In Progress",
    "last_analysis_reasoning": "Initial state",
    "system_notice": "Start the interview with profiling questions."
  },
  "user_profile": {},
  "needs_analysis": {},
  "product_assessment": {},
  "tech_strategy": {},
  "product_framework": {},
  "versioning_and_delivery": {},
  "deployment": {},
  "observability": {},
  "growth": {},
  "monetization": {},
  "evaluation": {},
  "decision_log": []
}

class AnalystAgent:
    """
    Analyst Agent (Backend Data Analyst)
    负责监听对话，更新 JSON 状态，并生成 System Notice 指导 Interviewer。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client if llm_client else LLMClient()

    async def analyze_turn(self, history: List[Dict[str, str]], current_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析最新一轮对话并更新状态。
        
        Args:
            history: 完整的对话历史 [{"role": "user", "content": "..."}, ...]
            current_state: 上一轮的 JSON 状态。如果为 None，使用 INITIAL_STATE。
            
        Returns:
            New JSON state.
        """
        if current_state is None:
            current_state = INITIAL_STATE

        state_str = json.dumps(current_state, ensure_ascii=False, indent=2)
        
        # 截取最近的对话上下文（避免 Token 溢出，但要保留足够信息）
        # 假设 Summary Agent 还没实现，我们先传最近 10 条
        recent_history = history[-10:] if len(history) > 10 else history
        history_str = json.dumps(recent_history, ensure_ascii=False, indent=2)

        user_input = f"""
### Previous JSON State (Must Increment based on this)
{state_str}

### Conversation History (Recent)
{history_str}

### Instruction
Analyze the latest turn and update the JSON state according to the System Prompt.
Ensure you generate a helpful `system_notice` in `interview_session` for the Interviewer.
"""

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        try:
            # 强制使用 JSON Mode
            response = await self.llm.chat_completion(
                messages=messages,
                json_mode=True
            )
            
            if isinstance(response, dict):
                return response
            elif isinstance(response, str):
                try:
                    new_state = json.loads(response)
                    return new_state
                except json.JSONDecodeError:
                    logger.error("Failed to parse Analyst JSON response")
                    return current_state
            else:
                return current_state
                
        except Exception as e:
            logger.error(f"Analyst analysis failed: {e}")
            return current_state
