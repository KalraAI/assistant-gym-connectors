"""LangGraph: a real two-node graph - 'negotiate' produces your message,
'gym' sends it to Assistant Gym and routes back or finishes."""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import gym_client

llm = ChatOpenAI(model="gpt-4.1-mini")

class GymState(TypedDict, total=False):
    gym_state: str          # opaque signed state token from the Gym
    opponent_reply: str
    history: list[dict]
    result: dict
    _msg: str

def negotiate(s: GymState) -> GymState:
    msgs = [("system", "You negotiate for your owner. Firm, factual, polite.")]
    msgs += [("assistant" if h["role"] == "agent" else "user", h["content"])
             for h in s["history"]]
    msg = llm.invoke(msgs).content
    return {"history": s["history"] + [{"role": "agent", "content": msg}],
            "_msg": msg}  # type: ignore

def gym(s: GymState) -> GymState:
    out = gym_client.turn(s["gym_state"], s["history"][-1]["content"])
    if gym_client.is_finished(out):
        if out.get("result") is None:
            raise RuntimeError("Gym ended without a result: " + str(out.get("status")))
        return {"gym_state": out.get("state", s["gym_state"]), "result": out["result"]}
    if out.get("reply") is None:
        raise RuntimeError("Gym gave no reply for an open run")
    return {"gym_state": out["state"], "opponent_reply": out["reply"],
            "history": s["history"] + [{"role": "opponent", "content": out["reply"]}]}

def route(s: GymState) -> Literal["negotiate", "__end__"]:
    return "__end__" if "result" in s else "negotiate"

g = StateGraph(GymState)
g.add_node("negotiate", negotiate)
g.add_node("gym", gym)
g.set_entry_point("negotiate")
g.add_edge("negotiate", "gym")
g.add_conditional_edges("gym", route)
app = g.compile()

run = gym_client.start_run("auto-insurance-renewal", "my-langgraph-agent")
final = app.invoke({"gym_state": run["state"], "opponent_reply": run["opening"],
                    "history": [{"role": "opponent", "content": run["opening"]}]})
print(final.get("result", {}).get("score"), final.get("result", {}).get("feedback"))
