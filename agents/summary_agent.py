import logging
from typing import Dict, List, Optional

from utils.llm_client import LLMClient
from prompts.summary_prompt import SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class SummaryAgent:
    """
    Summary Agent (Cognitive Compressor)
    负责压缩对话历史，提取长期记忆。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client if llm_client else LLMClient()
        self.current_summary = ""

    async def update_summary(self, new_chunk: List[Dict[str, str]]) -> str:
        """
        更新摘要。
        
        Args:
            new_chunk: 新增的对话片段
            
        Returns:
            str: 更新后的摘要文本
        """
        if not new_chunk:
            return self.current_summary

        chunk_str = ""
        for msg in new_chunk:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            chunk_str += f"{role}: {content}\n"

        user_input = f"""
### Old Summary
{self.current_summary}

### New Dialogue Chunk
{chunk_str}

### Instruction
Synthesize the Old Summary and New Dialogue Chunk into a single updated summary paragraph.
"""

        messages = [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        try:
            # Summary Agent 返回纯文本，不需要 JSON Mode
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
                top_p=0.5,
                reasoning_effort="low",
                json_mode=False
            )
            
            if isinstance(response, str):
                self.current_summary = response.strip()
                return self.current_summary
            else:
                logger.error("Summary Agent received non-string response")
                return self.current_summary
                
        except Exception as e:
            logger.error(f"Summary update failed: {e}")
            return self.current_summary

    def get_summary(self) -> str:
        return self.current_summary
