import pytest
import sys
import os
import logging

# 确保路径正确
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst_agent import AnalystAgent

# 真实调用测试 (Integration Test)
@pytest.mark.asyncio
async def test_analyst_real_call():
    print("\n[Test] Initializing Analyst Agent...")
    agent = AnalystAgent()
    
    # 模拟一个典型的模糊用户需求
    user_input_content = "我想做一个像光点一样的网站，可以拖拽，不要太复杂。"
    history = [{"role": "user", "content": user_input_content}]
    print(f"[Test] Input: {user_input_content}")
    
    # 调用 analyze_turn
    result = await agent.analyze_turn(history, None)
    
    print(f"[Test] Result Keys: {result.keys()}")
    
    # 验证结构 (Cognitive Schema)
    assert "schema_version" in result
    assert "interview_session" in result
    assert "missing_info" in result
    
    # 验证 System Notice 生成
    interview_session = result["interview_session"]
    assert "system_notice" in interview_session
    assert len(interview_session["system_notice"]) > 0
    
    print(f"\n--- System Notice ---\n{interview_session['system_notice']}")
    print(f"\n--- Missing Info ---\n{result['missing_info']}")

# 边界测试：极短输入
@pytest.mark.asyncio
async def test_analyst_short_input():
    agent = AnalystAgent()
    history = [{"role": "user", "content": "hi"}]
    
    result = await agent.analyze_turn(history, None)
    
    assert "interview_session" in result
    assert "system_notice" in result["interview_session"]
    # 即使输入很短，也应该生成引导性 Notice
    assert len(result["interview_session"]["system_notice"]) > 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_analyst_real_call())
