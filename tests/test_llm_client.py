import pytest
import asyncio
import os
import sys

# 将项目根目录加入 path，以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

@pytest.mark.asyncio
async def test_llm_connection():
    print("\n[Test] Initializing LLMClient...")
    try:
        client = LLMClient()
    except ValueError as e:
        pytest.fail(f"Initialization failed: {e}")
        return

    messages = [{"role": "user", "content": "Hello, who are you?"}]
    
    print(f"[Test] Sending message to {client.model_id}...")
    try:
        response = await client.chat_completion(messages)
        print(f"[Test] Response: {response}")
        assert isinstance(response, str)
        assert len(response) > 0
    except Exception as e:
        pytest.fail(f"Chat completion failed: {e}")

@pytest.mark.asyncio
async def test_json_mode():
    client = LLMClient()
    messages = [
        {"role": "system", "content": "You are a JSON generator. Output a valid JSON object with key 'result' and value 'success'."},
        {"role": "user", "content": "Generate JSON."}
    ]
    
    print("\n[Test] Testing JSON Mode...")
    try:
        response = await client.chat_completion(messages, json_mode=True)
        print(f"[Test] JSON Response: {response}")
        assert isinstance(response, dict)
        assert "result" in response
        assert response["result"] == "success"
    except Exception as e:
        pytest.fail(f"JSON mode failed: {e}")

if __name__ == "__main__":
    # 手动运行测试
    async def main():
        print("=== Running Manual Test ===")
        client = LLMClient()
        
        # 1. 简单对话
        print("\n1. Testing Simple Chat...")
        res = await client.chat_completion([{"role": "user", "content": "Say 'Maia is online' in English."}])
        print(f"Result: {res}")
        
        # 2. JSON 模式
        print("\n2. Testing JSON Mode...")
        res_json = await client.chat_completion(
            [{"role": "system", "content": "Output JSON: {\"status\": \"ok\"}"}, {"role": "user", "content": "Go"}],
            json_mode=True
        )
        print(f"Result: {res_json}")
        
    asyncio.run(main())
