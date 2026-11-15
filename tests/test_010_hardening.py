"""010: hardening in the growing-return node, the saved graphs and the reported result."""
import json, pathlib, sys, unittest
from importlib.util import spec_from_file_location, module_from_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load
_s = spec_from_file_location("core009", ROOT / "experiments" / "009_morphology_as_memory" / "core.py")
core = module_from_spec(_s); _s.loader.exec_module(core)
Grow = load(ROOT / "nodes" / "growing_return_node.py", "GrowingReturnNode")


def drive(node, site, n):
    for _ in range(n):
        node.pre_step(); node.set_input("pre_spike", 0.24); node.set_input("site_%d" % site, 1.0); node.step()


class TestHardening(unittest.TestCase):
    def test_off_by_default_and_hardness_stays_zero(self):
        n = Grow(); drive(n, 5, 20)
        self.assertEqual(n.harden_rate, 0.0)
        self.assertEqual(n.hardness, [0.0] * 8)

    def test_use_hardens_the_strong_branch_most_and_age_hardens_equally(self):
        u = Grow(); u.set_config_options({"learning_rate": 0.2, "harden_rate": 0.2, "harden_mode": 1, "prune_threshold": 0.0})
        a = Grow(); a.set_config_options({"learning_rate": 0.2, "harden_rate": 0.2, "harden_mode": 2, "prune_threshold": 0.0})
        drive(u, 5, 30); drive(a, 5, 30)
        self.assertEqual(max(range(8), key=lambda s: u.hardness[s]), 5)
        self.assertAlmostEqual(max(a.hardness), min(a.hardness))
        self.assertAlmostEqual(sum(u.hardness), sum(a.hardness), places=6)

    def test_hardened_body_changes_less_and_keeps_budget(self):
        def shift(rate):
            n = Grow(); n.set_config_options({"learning_rate": 0.2, "harden_rate": rate, "prune_threshold": 0.0})
            drive(n, 5, 40); w = list(n.weights); drive(n, 1, 40)
            self.assertAlmostEqual(sum(n.weights), 1.0, places=6)
            return sum(abs(x - y) for x, y in zip(w, n.weights))
        self.assertLess(shift(1.0), shift(0.0))

    def test_hardness_only_grows(self):
        n = Grow(); n.set_config_options({"harden_rate": 0.2})
        drive(n, 5, 10); h = list(n.hardness); drive(n, 2, 10)
        self.assertTrue(all(b >= a for a, b in zip(h, n.hardness)))


class TestGraphsAndReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = ROOT / "PerceptionLab"
        if not (cls.up / "nodes" / "wavefieldnode.py").exists():
            raise unittest.SkipTest("clone PerceptionLab inside PerceptionLabAI")
        cls.R = json.loads((ROOT / "results" / "010_hardening.json").read_text())

    def test_graphs_load(self):
        paths = sorted((ROOT / "workflows").glob("010_*.json"))
        self.assertEqual(len(paths), 2)
        for p in paths:
            obj = core.instantiate(json.loads(p.read_text()), self.up)
            self.assertEqual(obj[core.GROW_IDS[0]].harden_rate, 0.2)

    def test_receipt_matches_the_report(self):
        C, P = self.R["conditions"], self.R["paired"]
        self.assertFalse(self.R["dev_run"])
        self.assertGreaterEqual(C["use"]["before"]["accuracy"], 0.75)           # rule 1 passes
        self.assertGreater(P["use_vs_soft_after_10"]["sign_p"], 0.05)           # rule 2 fails
        self.assertGreater(C["age"]["after_20"]["correct"], C["use"]["after_20"]["correct"])
        self.assertLess(P["use_vs_age_after_20"]["sign_p"], 0.01)
        self.assertEqual(sum(c["clipped_frames"] for c in C.values()), 0)


if __name__ == "__main__":
    unittest.main()
