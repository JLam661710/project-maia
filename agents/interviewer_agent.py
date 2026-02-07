import logging
import json
from typing import Dict, Any, List, Optional

from utils.llm_client import LLMClient
from prompts.interviewer_prompt import INTERVIEWER_CORE_PROMPT, INTERVIEWER_INIT_INSTRUCTION

logger = logging.getLogger(__name__)

class InterviewerAgent:
    """
    Interviewer Agent 负责执行访谈计划。
    它维护对话上下文，并根据 Analyst 生成的动态指令 (System Notice) 进行提问。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm = llm_client if llm_client else LLMClient()
        self.history: List[Dict[str, str]] = []
        
        # 初始化对话历史，设置基础 System Prompt (Core + Init)
        full_prompt = f"{INTERVIEWER_CORE_PROMPT}\n\n{INTERVIEWER_INIT_INSTRUCTION}"
        self.history.append({"role": "system", "content": full_prompt})

    async def generate_reply(self, user_input: Optional[str] = None, system_notice: Optional[str] = None) -> str:
        """
        生成回复。
        
        Args:
            user_input: 用户的输入 (如果是第一轮可能为 None)
            system_notice: 来自 Analyst 的动态指令 (指导当前轮次的提问策略)
            
        Returns:
            AI 的回复
        """
        # 1. 如果有用户输入，先记录到历史
        if user_input:
            self.history.append({"role": "user", "content": user_input})
        
        # 2. 构建本次请求的消息列表
        messages = self.history.copy()
        
        # 3. 如果有动态指令，作为临时的 System Message 插入到最后
        # 这能确保模型在生成当前回复时优先考虑该指令
        if system_notice:
            messages.append({
                "role": "system", 
                "content": f"### SYSTEM NOTICE (Dynamic Instruction from Analyst)\n{system_notice}"
            })
            
        # 4. 调用 LLM
        response = await self.llm.chat_completion(messages=messages)
        
        # 5. 记录 AI 的回复到历史
        if isinstance(response, str):
            self.history.append({"role": "assistant", "content": response})
            
            # 动态 Prompt 管理: 如果是第一轮回复，移除启动指令
            assistant_msgs = [m for m in self.history if m["role"] == "assistant"]
            if len(assistant_msgs) == 1 and self.history[0]["role"] == "system":
                self.history[0]["content"] = INTERVIEWER_CORE_PROMPT
                logger.info("System prompt updated: Initialization instructions removed after first turn.")
                
            return response
        else:
            return "Error: Unexpected response format."
            
    def get_history(self) -> List[Dict[str, str]]:
        """
        获取完整对话历史
        """
        return self.history

    def get_visible_history(self) -> List[Dict[str, str]]:
        """
        获取去除 System Prompt 的对话历史 (用于展示)
        """
        return [msg for msg in self.history if msg["role"] != "system"]
