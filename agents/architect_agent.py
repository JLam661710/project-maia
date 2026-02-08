import logging
import json
from typing import Dict, Any, Optional

from utils.llm_client import LLMClient
from prompts.architect_prompt import ARCHITECT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ArchitectAgent:
    """
    Architect Agent (Solution Architect)
    负责在访谈结束后，基于 Analyst 生成的 JSON State 生成最终的 Markdown 方案。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm = llm_client if llm_client else LLMClient()

    async def generate_proposal(self, final_state: Dict[str, Any]) -> str:
        """
        基于最终状态生成方案文档。
        
        Args:
            final_state: 访谈结束后的完整 JSON State
            
        Returns:
            str: 包含多个文件边界的完整 Markdown 响应
        """
        state_str = json.dumps(final_state, ensure_ascii=False, indent=2)
        
        user_input = f"""
### Final JSON State
{state_str}

### Instruction
Based on the provided Final JSON State, generate the complete solution proposal files according to the System Prompt.
Ensure you use the `=== FILE: <file_name> ===` format strictly.
"""

        messages = [
            {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        try:
            logger.info("Architect Agent is generating the proposal...")
            # 注意：这里不使用 json_mode=True，因为我们需要生成 Markdown 文本
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.5, # 稍微提高一点创造性
                max_tokens=8192,
                top_p=0.7,
                reasoning_effort="high"
            )
            
            if isinstance(response, str):
                return response
            else:
                logger.error("Architect Agent received non-string response")
                return "Error: Failed to generate proposal."
                
        except Exception as e:
            logger.error(f"Architect generation failed: {e}")
            return f"Error: Architect generation failed: {e}"
