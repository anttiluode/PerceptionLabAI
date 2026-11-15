"""Build the 007 graphs from the measured 004 base graph (same field, units, thresholds)."""
import copy, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = json.loads((ROOT / "workflows" / "004_two_fades_one_field.json").read_text())

def gate(node_id, title, y, weight=1.0, learn=1, sign=1.0):
    return {"id": node_id, "class_name": "HomeostaticReturnGateNode",
            "pos_x": -30.0, "pos_y": y, "width": 325.0, "height": 170.0,
            "config": {"node_title": title, "weight": weight, "target_rate": 0.010,
                       "learning_rate": 0.02, "rate_tau": 200.0, "sign": sign,
                       "learn_enabled": learn},
            "custom_state_file": None}

def plotter(node_id, title, y):
    return {"id": node_id, "class_name": "SignalPlotterNode",
            "pos_x": 400.0, "pos_y": y, "width": 335.0, "height": 210.0,
            "config": {"node_title": title, "history_size": 500},
            "custom_state_file": None}

def edge(a, ap, b, bp, w=1):
    return {"from_node_id": a, "from_port": ap, "to_node_id": b, "to_port": bp,
            "learned_weight": w}

def build(a_gate=True, b_gate=False, a_weight=1.0, learn=1, sign=1.0, b_return=True):
    g = copy.deepcopy(BASE)
    edges = [e for e in g["edges"]
             if not (e["to_node_id"] == 1 and e["from_port"] == "pulse")]
    if a_gate:
        tag = "homeostatic" if learn and sign > 0 else ("ANTI control" if learn else "frozen")
        g["nodes"].append(gate(7, "A return / %s" % tag, 190.0, a_weight, learn, sign))
        edges += [edge(2, "pulse", 7, "pre_spike"), edge(7, "signal", 1, "write_0")]
    if b_return:
        if b_gate:
            g["nodes"].append(gate(8, "B return / homeostatic", 380.0, 1.0, learn, sign))
            edges += [edge(3, "pulse", 8, "pre_spike"), edge(8, "signal", 1, "write_2")]
        else:
            edges.append(edge(3, "pulse", 1, "write_2"))
    g["nodes"].append(plotter(9, "Red A weight / Green A rate over target"
                              + (" / Blue B weight" if b_gate else ""), 300.0))
    edges += [edge(7, "weight", 9, "signal_A (Red)"),
              edge(7, "rate_over_target", 9, "signal_B (Green)")]
    if b_gate and b_return:
        edges.append(edge(8, "weight", 9, "signal_C (Blue)"))
    g["edges"] = edges
    return g

GRAPHS = {
    "007_homeostatic_a_return.json": build(),
    "007_frozen_gate_full.json": build(learn=0),
    "007_anti_homeostatic_a.json": build(sign=-1.0, a_weight=0.30),
    "007_both_homeostatic.json": build(b_gate=True),
    "007_homeostatic_a_no_b_return.json": build(b_return=False),
}
if __name__ == "__main__":
    for name, g in GRAPHS.items():
        (ROOT / "workflows" / name).write_text(json.dumps(g, indent=2) + "\n")
        print("wrote", name)
