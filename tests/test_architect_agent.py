import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from agents.architect_agent import ArchitectAgent
from utils.llm_client import LLMClient

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=LLMClient)
    client.chat_completion = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_generate_proposal(mock_llm_client):
    # 1. 准备 Mock 数据
    agent = ArchitectAgent(llm_client=mock_llm_client)
    
    mock_state = {
        "user_profile": {"tech_level": "low", "role": "Content Creator"},
        "needs_analysis": {"core_pain_point": "Can't analyze data across platforms"},
        "tech_strategy": {"stack": "Coze + Feishu"}
    }
    
    expected_response = """=== FILE: DOC_01_PRD.md ===
# Product Requirement Document
...
=== FILE: DOC_02_Tech_Architecture.md ===
# Tech Stack
...
"""
    mock_llm_client.chat_completion.return_value = expected_response
    
    # 2. 执行测试
    result = await agent.generate_proposal(mock_state)
    
    # 3. 验证结果
    assert result == expected_response
    
    # 验证 LLM 调用参数
    call_args = mock_llm_client.chat_completion.call_args
    assert call_args is not None
    messages = call_args.kwargs['messages']
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert "Final JSON State" in messages[1]['content']
    assert "Coze + Feishu" in messages[1]['content']
