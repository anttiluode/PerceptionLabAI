"""Save host-loadable 009 graphs. Grown example bodies come from the committed receipt."""
import importlib.util, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("core009", ROOT / "experiments" / "009_morphology_as_memory" / "core.py")
core = importlib.util.module_from_spec(s); s.loader.exec_module(core)
R = json.loads((ROOT / "results" / "009_morphology_as_memory.json").read_text())
TH = [tuple(t) for t in R["calibration"]["thresholds"]]
GROW = R["settings"]["grow"]
def save(name, g):
    (ROOT / "workflows" / name).write_text(json.dumps(g, indent=2) + "\n"); print("wrote", name)
if __name__ == "__main__":
    for order, stim in (("AB", [("A", 20, 1.0), ("B", 52, 1.0)]), ("BA", [("B", 20, 1.0), ("A", 52, 1.0)])):
        save("009_%s_growing_one_episode.json" % order, core.build_graph(core.uniform_structure(), TH, stim, learn=1, params=GROW))
        save("009_probe_%s_grown_body.json" % order,
             core.build_graph(R["example_structures"]["0" + order], TH, None, probe_site=R["settings"]["probe_site"], learn=0, params=GROW))
    save("009_probe_naive_body.json", core.build_graph(core.uniform_structure(), TH, None, probe_site=R["settings"]["probe_site"], learn=0, params=GROW))
