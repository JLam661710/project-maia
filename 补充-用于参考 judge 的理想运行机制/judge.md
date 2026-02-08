import json
import os
import re
import streamlit as st
from utils.llm_client import llm_client
from utils.analytics import analytics


_SYSTEM_PROMPT = """你是一个隐藏在后台的评估者（Judge）。\n\n你不与用户直接对话。你的唯一任务是：在关键节点对“用户的想法/产品构想”进行评估与纠偏建议，并把建议以结构化 JSON 形式输出，供前台访谈者（Interviewer）调整提问策略。\n\n你评估的核心目标：\n1) 得到“具体且真实的需求/痛点/难题”。\n2) 区分“表面需求（工具形状）”与“本质需求（终极状态）”。\n3) 生成可执行的下一步追问清单（3-8 条），让 Interviewer 把对话拉回到证据与场景。\n\n判别标准：\n- 具体：形成“可复现的场景要素”，包含主角/触发时机/关键步骤/爆发点/坏结果。\n- 真实：可被测量的损失（时间/金钱机会/精力情绪）+ 是现状非幻想 + 具有不得不做的强制性或明显后果。\n\n重要说明：\n- “可复现”是你的内部评估方式，不要要求用户写任何脚本或长说明。\n\n输出要求：\n- 只输出一个 JSON 对象，严禁输出 Markdown 代码块。\n- 不要编造用户未说过的事实；不确定就写入 evidence_gaps。\n\n输出 JSON Schema：\n{\n  \"distilled_pain\": \"String, 去工具形状后的本质痛点陈述\",\n  \"surface_need\": \"String, 用户的工具形状/表面需求（可为空）\",\n  \"essence_need\": \"String, 用户渴望的终极状态/本质需求（可为空）\",\n  \"concreteness_signals\": [\"String, 已有的具体性证据\"],\n  \"reality_signals\": [\"String, 已有的真实性证据\"],\n  \"evidence_gaps\": [\"String, 还缺哪些关键证据\"],\n  \"scenario_gaps\": [\"String, 场景要素还缺什么（主角/时机/步骤/爆发点/坏结果）\"],\n  \"red_flags\": [\"String, 幻想/不真实/不具体等风险点\"],\n  \"next_questions\": [\"String, 给 Interviewer 的下一步追问（必须可直接问给用户，且低负担）\"],\n  \"correction_tone\": \"String, enum: ['gentle', 'neutral', 'challenging']\",\n  \"judge_notice\": \"String, 给 Interviewer 的一句话纠偏指令\"\n}\n"""


class JudgeAgent:
    def __init__(self):
        self.model = os.getenv("MODEL_JUDGE", "doubao-seed-1-8-251228")
        self.reasoning_effort = os.getenv("REASONING_EFFORT_JUDGE", "medium")

    def run(self, chat_history, current_json_state, context_summary=None, tool_catalog_injection=None):
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

        if tool_catalog_injection:
            messages.append({"role": "system", "content": str(tool_catalog_injection)})

        if context_summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"[PAST CONVERSATION SUMMARY]\\n{context_summary}",
                }
            )

        payload = {
            "chat_history": chat_history,
            "current_json_state": current_json_state,
        }

        messages.append(
            {
                "role": "user",
                "content": "请基于以下输入做评估并输出 JSON：\n" + json.dumps(payload, ensure_ascii=False),
            }
        )

        def _env_float(key: str, default):
            v = os.getenv(key)
            if v is None or v == "":
                return default
            try:
                return float(v)
            except Exception:
                return default

        def _env_int(key: str, default):
            v = os.getenv(key)
            if v is None or v == "":
                return default
            try:
                return int(v)
            except Exception:
                return default

        def _response_format_from_env(raw_value):
            if raw_value is None:
                return None
            raw_value = str(raw_value).strip()
            if not raw_value:
                return None
            if raw_value.lower() == "json_object":
                return {"type": "json_object"}
            try:
                obj = json.loads(raw_value)
                if isinstance(obj, dict) and str(obj.get("type", "")).strip().lower() == "json_object":
                    return {"type": "json_object"}
            except Exception:
                return None
            return None

        with st.spinner(f"Judge ({self.model}) is evaluating..."):
            kwargs = {}
            if self.reasoning_effort and self.reasoning_effort.lower() != "none":
                kwargs["reasoning_effort"] = self.reasoning_effort

            top_p = _env_float("TOP_P_JUDGE", None)
            if top_p is not None:
                kwargs["top_p"] = top_p

            presence_penalty = _env_float("PRESENCE_PENALTY_JUDGE", None)
            if presence_penalty is not None:
                kwargs["presence_penalty"] = presence_penalty

            frequency_penalty = _env_float("FREQUENCY_PENALTY_JUDGE", None)
            if frequency_penalty is not None:
                kwargs["frequency_penalty"] = frequency_penalty

            seed = _env_int("SEED_JUDGE", None)
            if seed is not None:
                kwargs["seed"] = seed

            response_format = _response_format_from_env(os.getenv("RESPONSE_FORMAT_JUDGE"))

            max_tokens = _env_int("MAX_TOKENS_JUDGE", None)
            temperature = _env_float("TEMPERATURE_JUDGE", 0.2) or 0.2

            response_text, _ = llm_client.get_completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                **kwargs,
            )

        try:
            user_id = "guest"
            if hasattr(st, "session_state") and "user_info" in st.session_state and st.session_state.user_info:
                user_id = st.session_state.user_info.id
            analytics.track_event(user_id, "judge_run", {"model": self.model})
        except Exception:
            pass

        if not response_text:
            return None

        text = response_text.strip()
        match = re.search(r"\{[\s\S]*\}", text)
        json_str = match.group(0) if match else text

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            st.error("Judge failed to produce valid JSON.")
            return None

        if isinstance(data, dict):
            return data

        return None
