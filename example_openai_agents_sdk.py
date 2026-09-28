"""OpenAI Agents SDK: hand the Gym to your agent as a tool."""
from agents import Agent, Runner, function_tool
import gym_client

_run = {}

@function_tool
def gym_start(scenario_id: str) -> str:
    """Start an Assistant Gym training run; returns the opponent's opening."""
    r = gym_client.start_run(scenario_id, "my-openai-agent")
    _run["state"] = r["state"]
    return r["opening"]

@function_tool
def gym_reply(message: str) -> str:
    """Send your next negotiation message; returns the opponent's reply or CLOSED+score."""
    out = gym_client.turn(_run["state"], message)
    _run["state"] = out.get("state", _run["state"])
    if gym_client.is_finished(out):
        if out.get("result") is None:
            raise RuntimeError("Gym ended without a run result")
        return "CLOSED: " + str(out["result"])
    if out.get("reply") is None:
        raise RuntimeError("Gym gave no reply for an open run")
    return out["reply"]

agent = Agent(name="gym-trainee", tools=[gym_start, gym_reply],
              instructions="Complete the Gym scenario to the best score, then stop.")
print(Runner.run_sync(agent, "Train me on auto-insurance-renewal").final_output)
