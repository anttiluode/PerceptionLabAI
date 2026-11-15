"""Save host-loadable 008 graphs. Self-tuned weights are read from the committed receipt."""
import importlib.util, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("lab008", ROOT / "experiments" / "008_self_tuned_order" / "run.py")
lab = importlib.util.module_from_spec(s); s.loader.exec_module(lab)
W = json.loads((ROOT / "results" / "008_self_tuned_order.json").read_text())["development"]["median_weights"]
TRIAL = (0, 32, 1.0)
def save(name, weights, learn, order):
    g = lab.lab005.prepare_trial(lab.build_graph(weights, learn=learn), order, TRIAL)
    g["nodes"].append({"id": 12, "class_name": "SignalPlotterNode", "pos_x": 1060.0, "pos_y": 520.0,
                       "width": 335.0, "height": 210.0,
                       "config": {"node_title": "Return weights: A (drawn blue) / B green / C (drawn red)", "history_size": 500},
                       "custom_state_file": None})
    for gid, port in ((9, "signal_A (Red)"), (10, "signal_B (Green)"), (11, "signal_C (Blue)")):
        g["edges"].append({"from_node_id": gid, "from_port": "weight", "to_node_id": 12, "to_port": port, "learned_weight": 1})
    (ROOT / "workflows" / name).write_text(json.dumps(g, indent=2) + "\n"); print("wrote", name)
if __name__ == "__main__":
    save("008_AB_self_tuning_live.json", lab.W_005B, 1, "AB")
    for o in ("AB", "BA"):
        save("008_%s_self_tuned_frozen.json" % o, W, 0, o)
        save("008_%s_fixed_gated.json" % o, lab.W_005B, 0, o)
