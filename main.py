import asyncio
import logging
import sys
import os
import re
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
from agents.architect_agent import ArchitectAgent
from agents.judge_agent import JudgeAgent
from agents.summary_agent import SummaryAgent

def save_proposal_files(proposal_text: str, output_dir: str = "output_proposal"):
    """
    解析 Architect 的输出并保存为多个文件。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Regex to find file boundaries: === FILE: filename ===
    # content...
    # Use non-capturing group (?:...) for the lookahead to avoid re.findall returning it
    pattern = r"=== FILE: (.*?) ===\n(.*?)(?=(?:=== FILE:|$))"
    matches = re.findall(pattern, proposal_text, re.DOTALL)
    
    if not matches:
        # Fallback: save entire text to one file if format is not found
        with open(f"{output_dir}/FULL_PROPOSAL.md", "w") as f:
            f.write(proposal_text)
        print(f"[System] Could not parse file boundaries. Saved full response to {output_dir}/FULL_PROPOSAL.md")
        return

    for filename, content in matches:
        filename = filename.strip()
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(content.strip())
        print(f"[System] Saved: {filepath}")

async def main():
    # Initialize all 5 Agents
    analyst = AnalystAgent()
    interviewer = InterviewerAgent()
    architect = ArchitectAgent()
    judge = JudgeAgent()
    summary_agent = SummaryAgent()
    
    current_state = None
    turn_count = 0
    SUMMARY_INTERVAL = 3  # Update summary every 3 turns
    
    # Judge Trigger Gates State
    judge_gate_counts = {
        "initial": 0,
        "correction": 0,
        "pre_completion": 0
    }
    
    # Keywords that suggest user is diving into tech details
    JUDGE_TRIGGER_KEYWORDS = [
        "cursor", "trae", "github", "gitlab", "supabase", "vercel", "aws", "docker", 
        "python", "js", "react", "vue", "nextjs", "fastapi", "数据库", "部署", "代码", 
        "支付", "订阅", "api", "key", "token"
    ]

    print("--- Maia Interview Session Started (5-Agent Collaboration Mode) ---")
    print("(Type 'quit', 'exit' or 'generate' to end the session)")

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
    # We need to handle the first input separately or initialize user_input properly
    # Actually, the logic below assumes we start with a user input loop, but now we moved input to the bottom.
    # Let's restructure:
    # 1. Start with initial system notice (done above)
    # 2. Loop starts by WAITING for user input (Initial turn)
    # 3. Then enters the async loop
    
    # But wait, the previous code had `user_input = input()` at the top of the loop.
    # In the Async Parallel model, we want:
    # Loop:
    #   A. Interviewer Reply (using current notice & user input)
    #   B. Async Analysis + Async User Input (Parallel)
    #   C. Sync Barrier
    #   D. Update Notice
    #   E. Repeat
    
    # The problem is the very first turn.
    # Turn 1:
    #   User Input (Needs to happen first)
    #   Interviewer Reply
    #   Async Analysis + User Input (for Turn 2) ...
    
    # So we need an initial user input before the loop.
    try:
        user_input = input("\n[User]: ").strip()
    except EOFError:
        return

    while True:
        if not user_input:
             # Handle empty input if needed, or just ask again
             try:
                user_input = input("\n[User]: ").strip()
                continue
             except EOFError:
                break
            
        if user_input.lower() in ["quit", "exit", "generate"]:
            print("Session ended.")
            break
        
        turn_count += 1
            
        # 3. Interviewer Responds IMMEDIATELY (The Mouth)
        # Using system_notice from previous turn (or initial)
        print("\n[Maia] Speaking...") 
        reply = await interviewer.generate_reply(user_input=user_input, system_notice=system_notice)
        print(f"[Maia]: {reply}")

        # 4. Async Parallel Pipeline: Unlock Input vs Background Analysis
        print(f"\n[System] Input Unlocked (You can reply now while Analyst thinks in background)...")
        
        # Prepare background task (Analyst + Judge)
        visible_history = interviewer.get_visible_history()
        history_for_analyst = visible_history
        
        async def run_background_analysis(history, state):
            print("[Background] Analyst started...")
            new_state = await analyst.analyze_turn(history, state)
            
            # Run Judge if needed
            run_judge = False
            trigger_reasons = []
            
            if new_state.get("needs_judge_review", False):
                run_judge = True
                trigger_reasons.append(f"Analyst Request")
            
            if turn_count == 2 and judge_gate_counts["initial"] == 0:
                run_judge = True
                trigger_reasons.append("Initial Gate")
                judge_gate_counts["initial"] += 1
                
            readiness = new_state.get("completion_readiness", 0)
            status = new_state.get("status")
            if (status == "Completed" or readiness >= 80) and judge_gate_counts["pre_completion"] == 0:
                run_judge = True
                trigger_reasons.append("Pre-completion Gate")
                judge_gate_counts["pre_completion"] += 1
                
            user_hits_keyword = any(k in user_input.lower() for k in JUDGE_TRIGGER_KEYWORDS)
            missing_info_str = str(new_state.get("missing_info", [])).lower()
            has_critical_gaps = "scenario" in missing_info_str or "loss" in missing_info_str or "pain" in missing_info_str
            
            if turn_count >= 4 and user_hits_keyword and has_critical_gaps and judge_gate_counts["correction"] == 0:
                run_judge = True
                trigger_reasons.append("Correction Gate")
                judge_gate_counts["correction"] += 1
            
            judge_res = None
            if run_judge:
                print(f"[Background] Judge running ({', '.join(trigger_reasons)})...")
                judge_res = await judge.evaluate_turn(history, new_state)
            
            # Summary Check
            if turn_count % SUMMARY_INTERVAL == 0:
                 print("[Background] Summary compressing...")
                 await summary_agent.update_summary(history)
                 
            print("[Background] All tasks finished. Ready for next turn.")
            return new_state, judge_res

        # Create background task
        analysis_task = asyncio.create_task(run_background_analysis(history_for_analyst, current_state))
        
        # 5. Wait for User Input (Main Thread)
        # This input() is blocking, but analysis_task runs in background event loop?
        # WAIT: In Python's default asyncio event loop, `input()` blocks the WHOLE loop!
        # We must use run_in_executor to make input() non-blocking for the loop.
        
        loop = asyncio.get_running_loop()
        try:
            # Show prompt without newline to mimic shell
            print("\n[User]: ", end="", flush=True)
            user_input = await loop.run_in_executor(None, sys.stdin.readline)
            user_input = user_input.strip()
        except EOFError:
            break
            
        if not user_input:
             # If user just hits enter, we still need to wait for analysis? 
             # Let's assume valid input.
             pass

        # 6. Synchronization Barrier (Rendezvous)
        # User has spoken. Now we MUST have the analysis result to proceed.
        if not analysis_task.done():
            print("\n[System] Input received. Waiting for background analysis to finish...")
            current_state, judge_report = await analysis_task
        else:
            # Analysis finished before user input
            current_state, judge_report = await analysis_task
            
        # 7. Update System Notice for NEXT turn
        system_notice = current_state["interview_session"].get("system_notice", "Continue interview.")
        if judge_report:
            judge_notice = judge_report.get("judge_notice", "")
            next_questions = judge_report.get("next_questions", [])
            if judge_notice:
                system_notice = f"{system_notice}\n\n[JUDGE WARNING]: {judge_notice}\n[SUGGESTED QUESTIONS]: {next_questions}"
        
        # Check for completion status to notify user
        if current_state.get("status") == "Completed":
             print("\n\033[92m[System] 🎯 Analyst indicates the interview is complete! You can type 'generate' to create the proposal, or continue chatting.\033[0m")

        if user_input.lower() in ["quit", "exit", "generate"]:
             break
             
        # Loop continues -> Interviewer replies using the NEW system_notice
        continue

    # --- Generation Phase ---
    if current_state:
        choice = input("\n[System] Do you want to generate the solution proposal now? (y/n): ").strip().lower()
        if choice == 'y':
            print("\n[Architect] Generating proposal... (This may take a minute)")
            proposal = await architect.generate_proposal(current_state)
            save_proposal_files(proposal)
            print("\n[System] All documents generated successfully in 'output_proposal' directory.")
        else:
            print("[System] Skipped proposal generation.")

if __name__ == "__main__":
    asyncio.run(main())
