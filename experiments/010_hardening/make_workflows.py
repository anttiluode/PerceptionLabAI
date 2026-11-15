"""Save host-loadable 010 graphs: one growing episode with hardening by use, and one by age."""
import importlib.util, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("core009", ROOT / "experiments" / "009_morphology_as_memory" / "core.py")
core = importlib.util.module_from_spec(s); s.loader.exec_module(core)
R9 = json.loads((ROOT / "results" / "009_morphology_as_memory.json").read_text())
R10 = json.loads((ROOT / "results" / "010_hardening.json").read_text())
TH = [tuple(t) for t in R9["calibration"]["thresholds"]]
if __name__ == "__main__":
    for name, mode in (("use", 1), ("age", 2)):
        P = dict(R10["grow"], harden_rate=R10["harden_rate"], harden_mode=mode)
        g = core.build_graph(core.uniform_structure(), TH, [("A", 20, 1.0), ("B", 52, 1.0)], learn=1, params=P)
        (ROOT / "workflows" / ("010_AB_growing_hardening_by_%s.json" % name)).write_text(json.dumps(g, indent=2) + "\n")
        print("wrote", name)
