import logging
import json
from typing import Dict, List, Optional, Any

from utils.llm_client import LLMClient
from prompts.judge_prompt import JUDGE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class JudgeAgent:
    """
    Judge Agent (The Evaluator)
    负责评估对话质量，识别风险，并为 Interviewer 提供纠偏建议。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client if llm_client else LLMClient()

    async def evaluate_turn(self, history: List[Dict[str, str]], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估当前对话轮次。
        
        Args:
            history: 最近的对话历史
            current_state: Analyst 生成的当前状态
            
        Returns:
            Dict: 包含风险评估和建议的 JSON 对象
        """
        
        # 提取关键信息用于 Prompt
        state_snippet = {
            "needs_analysis": current_state.get("needs_analysis", {}),
            "missing_info": current_state.get("missing_info", [])
        }
        
        state_str = json.dumps(state_snippet, ensure_ascii=False, indent=2)
        history_str = json.dumps(history[-5:], ensure_ascii=False, indent=2) # 只看最近 5 轮

        user_input = f"""
### Current Analyst State Snippet
{state_str}

### Recent Conversation
{history_str}

### Instruction
Analyze the recent conversation and the current state. 
Identify if the user is being vague, unrealistic, or if we are missing critical evidence.
Generate a JSON evaluation report.
"""

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=2048,
                top_p=0.1,
                reasoning_effort="medium",
                json_mode=True
            )
            
            if isinstance(response, dict):
                return response
            elif isinstance(response, str):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.error("Failed to parse Judge JSON response")
                    return {}
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return {}
