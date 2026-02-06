import pytest
import sys
import os
import asyncio

# 确保路径正确
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.interviewer_agent import InterviewerAgent

# 模拟 Analyst 的输出
MOCK_PLAN = {
    "analysis": "User wants a minimalist portfolio website with drag-and-drop features, inspired by 'Guangdian'.",
    "user_profile": {
        "role": "Designer/Student",
        "tech_level": "Low",
        "emotional_state": "Excited"
    },
    "pain_points": ["Complexity", "Technical barriers"],
    "interview_questions": [
        "What specific content do you want to showcase (images, videos, text)?",
        "Do you have a reference link for 'Guangdian' so I can understand the visual style?",
        "Is this for a personal portfolio or a commercial project?"
    ]
}

@pytest.mark.asyncio
async def test_interviewer_flow():
    print("\n[Test] Initializing Interviewer Agent...")
    agent = InterviewerAgent()
    
    # 1. Start Interview (Simulate Analyst's first notice)
    print("[Test] Starting Interview...")
    start_notice = "Start the interview with profiling questions."
    greeting = await agent.generate_reply(user_input=None, system_notice=start_notice)
    print(f"Agent: {greeting}")
    assert len(greeting) > 0
    
    # 2. User Answer 1
    user_msg_1 = "主要是放一些我的摄影作品，图片为主。"
    print(f"\nUser: {user_msg_1}")
    follow_notice = "Ask about the visual style and interactivity."
    response_1 = await agent.generate_reply(user_input=user_msg_1, system_notice=follow_notice)
    print(f"Agent: {response_1}")
    assert len(response_1) > 0
    
    # 3. User Answer 2
    user_msg_2 = "光点就是一个设计工作室的网站，我很喜欢那种漂浮的感觉。"
    print(f"\nUser: {user_msg_2}")
    final_notice = "Summarize the requirements and close the interview."
    response_2 = await agent.generate_reply(user_input=user_msg_2, system_notice=final_notice)
    print(f"Agent: {response_2}")
    assert len(response_2) > 0
    
    # 验证历史记录
    # 期望: Assistant(Greeting) -> User -> Assistant -> User -> Assistant
    history = agent.get_visible_history()
    print(f"\nHistory Length: {len(history)}")
    assert len(history) == 5 

if __name__ == "__main__":
    asyncio.run(test_interviewer_flow())
