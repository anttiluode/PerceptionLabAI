"""009: the growing-return node, its saved graphs, and the claims made from the receipt."""
import json, pathlib, sys, unittest
from importlib.util import spec_from_file_location, module_from_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load
_s = spec_from_file_location("core009", ROOT / "experiments" / "009_morphology_as_memory" / "core.py")
core = module_from_spec(_s); _s.loader.exec_module(core)
Grow = load(ROOT / "nodes" / "growing_return_node.py", "GrowingReturnNode")


def step(node, pre=0.0, sites=None):
    node.pre_step()
    if pre:
        node.set_input("pre_spike", pre)
    for s, v in (sites or {}).items():
        node.set_input("site_%d" % s, v)
    node.step()


class TestNode(unittest.TestCase):
    def test_output_is_pulse_times_weight_and_budget_is_kept(self):
        n = Grow()
        step(n, 0.24)
        self.assertAlmostEqual(sum(n.weights), 1.0)
        self.assertAlmostEqual(n.get_output("out_3"), 0.24 / 8)

    def test_grows_toward_the_busy_site_and_keeps_budget(self):
        n = Grow(); n.set_config_options({"learning_rate": 0.2})
        for _ in range(30):
            step(n, 0.0, {5: 1.0})
        for _ in range(5):
            step(n, 0.24, {5: 1.0})
        self.assertEqual(max(range(8), key=lambda s: n.weights[s]), 5)
        self.assertAlmostEqual(sum(n.weights), 1.0)

    def test_pruned_branches_never_return(self):
        n = Grow(); n.set_config_options({"learning_rate": 0.5})
        for _ in range(40):
            step(n, 0.24, {5: 1.0})
        dead = [s for s in range(8) if not n.alive[s]]
        self.assertTrue(dead)
        for _ in range(200):
            step(n, 0.24, {dead[0]: 5.0})
        self.assertEqual(n.weights[dead[0]], 0.0)
        self.assertGreaterEqual(sum(n.alive), 1)

    def test_no_pruning_when_threshold_is_zero_and_no_change_when_off(self):
        n = Grow(); n.set_config_options({"learning_rate": 0.5, "prune_threshold": 0.0})
        for _ in range(40):
            step(n, 0.24, {5: 1.0})
        self.assertEqual(sum(n.alive), 8)
        m = Grow(); m.set_config_options({"learn_enabled": 0})
        for _ in range(40):
            step(m, 0.24, {5: 1.0})
        self.assertEqual(m.weights, [1.0 / 8] * 8)

    def test_only_local_inputs(self):
        self.assertEqual(sorted(Grow().inputs), sorted(["pre_spike"] + ["site_%d" % s for s in range(8)]))


class TestGraphsAndReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = ROOT / "PerceptionLab"
        if not (cls.up / "nodes" / "wavefieldnode.py").exists():
            raise unittest.SkipTest("clone PerceptionLab inside PerceptionLabAI")
        cls.R = json.loads((ROOT / "results" / "009_morphology_as_memory.json").read_text())

    def test_saved_graphs_load_with_real_ports(self):
        paths = sorted((ROOT / "workflows").glob("009_*.json"))
        self.assertEqual(len(paths), 5)
        for p in paths:
            core.instantiate(json.loads(p.read_text()), self.up)

    def test_a_wipe_keeps_only_structure(self):
        th = [tuple(t) for t in self.R["calibration"]["thresholds"]]
        r1 = core.episode(core.uniform_structure(), th, self.up, "AB", 32, 1.0, 200)
        obj = core.instantiate(core.build_graph(r1["structure"], th, None, learn=0), self.up)
        self.assertEqual(float(abs(obj[2].field).max()), 0.0)
        self.assertEqual([obj[g].weights for g in core.GROW_IDS], r1["structure"]["weights"])
        self.assertTrue(all(obj[u].trace == 0.0 for u in core.UNIT_IDS))

    def test_receipt_matches_the_report(self):
        q2 = self.R["Q2_probe_decoding"]
        self.assertFalse(self.R["dev_run"])
        self.assertGreaterEqual(q2["grown"]["300"]["accuracy"], 0.75)
        self.assertEqual(q2["growth_off"]["300"]["correct"] * 2, q2["growth_off"]["300"]["of"])
        self.assertLessEqual(q2["shuffled_arrangement"]["300"]["accuracy"], 0.65)
        q3 = self.R["Q3_cue_completion"]
        self.assertGreater(q3["cue_A_far_site_energy"]["pairs_BA_higher"], q3["cue_A_far_site_energy"]["pairs_AB_higher"])
        self.assertGreater(self.R["Q4_interference"]["paired"]["sign_p"], 0.05)
        self.assertEqual(self.R["Q1_structure"]["clipped_frames_total"], 0)


if __name__ == "__main__":
    unittest.main()
