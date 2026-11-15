"""007: the homeostatic return gate, its saved graphs and its two decisive controls."""
import json
import pathlib
import sys
import unittest
from importlib.util import spec_from_file_location, module_from_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load

_s = spec_from_file_location("lab007", ROOT / "experiments" / "007_homeostatic_return" / "run.py")
lab007 = module_from_spec(_s); _s.loader.exec_module(lab007)
Gate = load(ROOT / "nodes" / "homeostatic_return_gate_node.py", "HomeostaticReturnGateNode")


def drive(gate, pattern):
    out = []
    for v in pattern:
        gate.pre_step()
        if v:
            gate.set_input("pre_spike", v)
        gate.step()
        out.append(gate.get_output("signal"))
    return out


class TestGateNode(unittest.TestCase):
    def test_passes_pulse_times_weight(self):
        g = Gate(); g.set_config_options({"weight": 0.4, "learn_enabled": 0})
        self.assertEqual(drive(g, [0, 0.24, 0]), [0.0, 0.24 * 0.4, 0.0])
        self.assertEqual(g.weight, 0.4)

    def test_frequent_firing_lowers_weight(self):
        g = Gate()
        drive(g, [0.24 if t % 20 == 0 else 0 for t in range(2000)])   # 0.05 > target 0.01
        self.assertLess(g.weight, 0.9)

    def test_rare_firing_raises_weight(self):
        g = Gate(); g.set_config_options({"weight": 0.3})
        drive(g, [0.24 if t % 500 == 0 else 0 for t in range(2000)])  # 0.002 < target
        self.assertGreater(g.weight, 0.3)

    def test_sign_flips_direction(self):
        g = Gate(); g.set_config_options({"weight": 0.5, "sign": -1.0})
        drive(g, [0.24 if t % 20 == 0 else 0 for t in range(2000)])
        self.assertGreater(g.weight, 0.5)

    def test_weight_stays_bounded_and_has_no_other_input(self):
        g = Gate()
        self.assertEqual(list(g.inputs), ["pre_spike"])
        drive(g, [0.24] * 5000)
        self.assertGreaterEqual(g.weight, 0.0)
        drive(g, [0] * 20000)
        self.assertLessEqual(g.weight, 1.0)


class TestGraphs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ROOT / "PerceptionLab"
        if not (cls.upstream / "nodes" / "wavefieldnode.py").exists():
            raise unittest.SkipTest("clone PerceptionLab inside PerceptionLabAI")
        cls.graphs = {p.name: json.loads(p.read_text())
                      for p in (ROOT / "workflows").glob("007_*.json")}

    def test_five_graphs_load_with_real_ports(self):
        self.assertEqual(len(self.graphs), 5)
        for name, g in self.graphs.items():
            with self.subTest(name=name):
                obj, cls = lab007.prepare(g, self.upstream)
                self.assertEqual(obj[1].field.shape, (96, 96))
                self.assertEqual(cls[7], "HomeostaticReturnGateNode")

    def test_units_and_thresholds_are_the_004_ones(self):
        base = json.loads((ROOT / "workflows" / "004_two_fades_one_field.json").read_text())
        b = {n["id"]: n["config"] for n in base["nodes"]}
        for name, g in self.graphs.items():
            c = {n["id"]: n["config"] for n in g["nodes"]}
            for i in (0, 1, 2, 3):
                self.assertEqual(c[i], b[i], name)

    def test_a_reaches_the_field_only_through_the_gate(self):
        for name, g in self.graphs.items():
            direct = [e for e in g["edges"] if e["from_node_id"] == 2 and e["to_node_id"] == 1]
            self.assertEqual(direct, [], name)
            self.assertTrue(any(e["from_node_id"] == 7 and e["to_node_id"] == 1
                                and e["to_port"] == "write_0" for e in g["edges"]), name)

    def test_homeostatic_rescues_b_and_frozen_does_not(self):
        learn = lab007.run_graph(self.graphs["007_homeostatic_a_return.json"], self.upstream, 2400)
        fixed = lab007.run_graph(self.graphs["007_frozen_gate_full.json"], self.upstream, 2400)
        self.assertGreater(learn["quarter_spikes"]["B"][3], 0)
        self.assertTrue(learn["weights"]["A"]["final_in_004_band"])
        self.assertEqual(fixed["quarter_spikes"]["B"], [0, 0, 0, 0])
        self.assertEqual(fixed["weights"]["A"]["final"], 1.0)
        self.assertEqual(learn["clip_frames"], 0)

    def test_isolated_homeostatic_loop_dies(self):
        r = lab007.run_graph(self.graphs["007_homeostatic_a_no_b_return.json"], self.upstream, 3000)
        self.assertEqual(r["quarter_spikes"]["A"][3], 0)


if __name__ == "__main__":
    unittest.main()
