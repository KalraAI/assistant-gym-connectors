"""AutoGen/AG2: register the Gym as a tool on your assistant agent."""
from gym_client import start_run, turn, close, is_finished
import autogen

assistant = autogen.AssistantAgent("trainee", llm_config={"model": "gpt-4.1-mini"})

def gym_message(history_text: str) -> str:
    return assistant.generate_reply([{"role": "user", "content": history_text}])

run = start_run("service-bill-retention", "my-autogen-agent")
state, reply = run["state"], run["opening"]
history = []
for _ in range(20):
    msg = gym_message("\n".join(history + [f"Counterparty: {reply}"]))
    out = turn(state, msg)
    state = out.get("state", state)
    if is_finished(out):
        if out.get("result") is None: raise RuntimeError("Gym ended without a run result")
        print(out["result"]); break
    reply = out.get("reply")
    if reply is None: raise RuntimeError("Gym gave no reply for an open run")
    history += [f"Me: {msg}", f"Counterparty: {reply}"]
else:
    print(close(state, "walk")["result"])
