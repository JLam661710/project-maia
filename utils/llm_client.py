import os
import json
import logging
from typing import List, Dict, Any, Union, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError

# 加载 .env
load_dotenv()

# 配置日志
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)

class LLMClient:
    """
    封装 Doubao (OpenAI Compatible) API 的客户端。
    支持文本生成、JSON Mode 和流式输出。
    """
    
    def __init__(self):
        self.api_key = os.getenv("ARK_API_KEY")
        self.model_id = os.getenv("LLM_MODEL_ID")
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        
        if not self.api_key or not self.model_id:
            logger.error("ARK_API_KEY or LLM_MODEL_ID not found in environment variables.")
            raise ValueError("Missing LLM configuration.")

        # 初始化 AsyncOpenAI 客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info(f"LLMClient initialized with Model ID: {self.model_id}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        json_mode: bool = False,
        stream: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        发送聊天请求。
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 随机度 (0.0 - 1.0)
            max_tokens: 最大输出长度
            json_mode: 是否强制输出 JSON 格式
            stream: 是否流式输出 (暂不支持, 这里仅预留接口)
            
        Returns:
            生成的文本内容 或 解析后的 JSON 对象
        """
        try:
            response_format = {"type": "json_object"} if json_mode else None
            
            logger.debug(f"Sending request to LLM (json_mode={json_mode})...")
            
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                stream=stream
            )

            content = response.choices[0].message.content
            
            if json_mode:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {content}")
                    # 简单的容错：尝试在 ```json 和 ``` 之间提取
                    if "```json" in content:
                        import re
                        match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                        if match:
                            return json.loads(match.group(1))
                    raise ValueError("LLM response is not valid JSON.")
            
            return content

        except OpenAIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            raise

# 单例模式 (可选)
# client = LLMClient()
