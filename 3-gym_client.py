"""Assistant Gym client - zero dependencies (standard library only).

Runs an assistant policy through the Gym's public API. Core HTTP flow verified live against
https://hub.assistantgym.com/api/v1 on 2026-09-28.

Response shapes (observed):
  POST /runs  -> {run_id, state, opening, status, receipt_key, scenario, ...}
  POST /turns -> {status, turn, state, reply?}          reply absent on auto-close
  POST /close -> {status, result: {certificate, score, feedback, audit_chain?}}

A run is finished when a response carries "result" or its status != "open".
Docs: https://assistantgym.com/developers/
"""
import json
import urllib.request

BASE = "https://hub.assistantgym.com/api/v1"


def _post(path, body, timeout=60):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def scenarios():
    with urllib.request.urlopen(BASE + "/scenarios", timeout=30) as r:
        return json.load(r)["scenarios"]


def start_run(scenario_id, agent_id, seed=None):
    body = {"scenario_id": scenario_id, "agent_id": agent_id}
    if seed is not None:
        body["seed"] = seed
    return _post("/runs", body, timeout=30)


def turn(state, message):
    return _post("/turns", {"state": state, "message": message})


def close(state, outcome="accept"):
    return _post("/close", {"state": state, "outcome": outcome}, timeout=30)


def is_finished(resp):
    return resp.get("result") is not None or resp.get("status") not in (None, "open")


def train(agent_id, scenario_id, policy, max_turns=25):
    """Drive one full run. policy(history, opponent_reply) -> your next message.

    history: list of {"role": "opponent"|"agent", "content": str}
    Returns the run result dict (score, feedback, signed run record).
    """
    run = start_run(scenario_id, agent_id)
    state, reply, history = run["state"], run["opening"], []
    for _ in range(max_turns):
        history.append({"role": "opponent", "content": reply})
        msg = policy(history, reply)
        history.append({"role": "agent", "content": msg})
        out = turn(state, msg)
        state = out["state"]
        if is_finished(out):
            if out.get("result") is None:
                raise RuntimeError("Gym run ended without result; do not close twice: " + str(out.get("status")))
            return out["result"]
        reply = out.get("reply")
        if reply is None:  # defensive: no reply and not finished
            raise RuntimeError("Gym gave no reply for an open run")
    return close(state, outcome="walk")["result"]
