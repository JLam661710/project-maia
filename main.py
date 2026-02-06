import asyncio
import logging
import sys
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Suppress noisy logs from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)

from agents.analyst_agent import AnalystAgent
from agents.interviewer_agent import InterviewerAgent

async def main():
    analyst = AnalystAgent()
    interviewer = InterviewerAgent()
    current_state = None

    print("--- Maia Interview Session Started ---")
    print("(Type 'quit' or 'exit' to end the session)")

    # --- Initial Turn (AI starts) ---
    print("\n[System] Initializing session...")
    
    # 1. Analyst generates initial state and notice
    # Passing empty history to trigger initial state generation
    current_state = await analyst.analyze_turn([], None)
    system_notice = current_state["interview_session"].get("system_notice", "Start the interview.")
    
    print(f"\n[Analyst Notice]: {system_notice}")
    
    # 2. Interviewer generates opening
    reply = await interviewer.generate_reply(user_input=None, system_notice=system_notice)
    print(f"\n[Maia]: {reply}")

    # --- Main Loop ---
    while True:
        try:
            user_input = input("\n[User]: ").strip()
        except EOFError:
            break

        if not user_input:
            continue
            
        if user_input.lower() in ["quit", "exit"]:
            print("Session ended.")
            break
            
        # 3. Prepare history for Analyst
        # We need to simulate the new state of history including the user's latest input
        # because Interviewer hasn't processed it yet.
        visible_history = interviewer.get_visible_history()
        history_for_analyst = visible_history + [{"role": "user", "content": user_input}]
        
        # 4. Analyst Thinks
        print("\n[Analyst] Analyzing...")
        current_state = await analyst.analyze_turn(history_for_analyst, current_state)
        
        system_notice = current_state["interview_session"].get("system_notice", "Continue interview.")
        missing_info = current_state.get("missing_info", [])
        
        print(f"[Analyst Notice]: {system_notice}")
        print(f"[Analyst Status]: Missing Info: {missing_info}")

        # 5. Interviewer Responds
        # Now we pass the user input to Interviewer, who will record it and generate a reply
        # guided by the system_notice we just got.
        reply = await interviewer.generate_reply(user_input=user_input, system_notice=system_notice)
        print(f"\n[Maia]: {reply}")

if __name__ == "__main__":
    asyncio.run(main())
