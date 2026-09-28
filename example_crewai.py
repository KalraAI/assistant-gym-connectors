"""CrewAI: let a Crew agent play the trainee side."""
from gym_client import start_run, turn, close, is_finished
from crewai import Agent, Task, Crew

negotiator = Agent(role="Consumer advocate", goal="Get the best outcome for your principal",
                   backstory="Trained on real dispute playbooks.", verbose=False)

run = start_run("homeowners-water-damage", "my-crew")
state, reply = run["state"], run["opening"]
for _ in range(20):
    task = Task(description=f"Counterparty said: {reply}\nRespond with your next message only.",
                agent=negotiator, expected_output="One negotiation message.")
    msg = Crew(agents=[negotiator], tasks=[task]).kickoff().raw
    out = turn(state, msg)
    state = out.get("state", state)
    if is_finished(out):
        if out.get("result") is None: raise RuntimeError("Gym ended without a run result")
        print(out["result"]); break
    reply = out.get("reply")
    if reply is None: raise RuntimeError("Gym gave no reply for an open run")
else:
    print(close(state, "walk")["result"])
