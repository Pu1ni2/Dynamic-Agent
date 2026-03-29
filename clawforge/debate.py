import json
from .config import DEBATE_MODEL, MAX_ROUNDS
from .llm_client import call_llm_json


def _emit(emitter, event: dict):
    if emitter:
        try:
            emitter(event)
        except Exception:
            pass


def run_debate(task: str, generator_prompt: str, critic_prompt: str,
               modified_key: str, input_context: str = "",
               emitter=None, phase_name: str = "") -> dict:
    history = []
    result = None
    user_content = f"Task: {task}"
    if input_context:
        user_content += f"\n\n{input_context}"

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n  Round {round_num}/{MAX_ROUNDS}")
        _emit(emitter, {"type": "debate_round", "phase": phase_name, "round": round_num})

        # Generator (DA) proposes
        gen_messages = _build_messages(user_content, history, "generator")
        gen_messages.insert(0, {"role": "system", "content": generator_prompt})

        try:
            gen_response = call_llm_json(DEBATE_MODEL, gen_messages)
        except Exception as e:
            print(f"  [DA] Error: {e}")
            if result is None:
                raise RuntimeError(f"DA failed on round {round_num}: {e}") from e
            break

        history.append({"role": "generator", "content": json.dumps(gen_response)})
        result = gen_response
        print(f"  [DA] Proposed")
        _emit(emitter, {
            "type": "da_message",
            "phase": phase_name,
            "content": json.dumps(gen_response, indent=2),
        })

        # Critic (Evaluator) reviews
        crit_messages = _build_messages(user_content, history, "critic")
        crit_messages.insert(0, {"role": "system", "content": critic_prompt})

        try:
            crit_response = call_llm_json(DEBATE_MODEL, crit_messages)
        except Exception as e:
            print(f"  [Evaluator] Error: {e}")
            break  # result is at least the gen_response here, so safe to fall through

        history.append({"role": "critic", "content": json.dumps(crit_response)})

        approved = crit_response.get("approved", False)
        critique = crit_response.get("critique", "")
        _emit(emitter, {
            "type": "evaluator_message",
            "phase": phase_name,
            "content": json.dumps(crit_response, indent=2),
            "approved": approved,
            "critique": critique,
        })

        if approved:
            print(f"  [Evaluator] APPROVED")
            _emit(emitter, {"type": "debate_approved", "phase": phase_name})
            return crit_response.get(modified_key, result)

        result = crit_response.get(modified_key, result)
        print(f"  [Evaluator] REJECTED — {critique[:100]}")

    print(f"  Max rounds reached. Using last version.")
    _emit(emitter, {"type": "debate_approved", "phase": phase_name})
    return result


def _build_messages(user_content: str, history: list, speaker: str) -> list:
    messages = [{"role": "user", "content": user_content}]
    for entry in history:
        role = "assistant" if entry["role"] == speaker else "user"
        messages.append({"role": role, "content": entry["content"]})
    return messages
