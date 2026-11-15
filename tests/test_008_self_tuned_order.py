"""008: graphs load with real ports, frozen gates stay frozen, and the receipt says what the report says."""
import json, pathlib, sys, unittest
from importlib.util import spec_from_file_location, module_from_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
_s = spec_from_file_location("lab008", ROOT / "experiments" / "008_self_tuned_order" / "run.py")
lab = module_from_spec(_s); _s.loader.exec_module(lab)


class Test008(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = ROOT / "PerceptionLab"
        if not (cls.up / "nodes" / "wavefieldnode.py").exists():
            raise unittest.SkipTest("clone PerceptionLab inside PerceptionLabAI")
        cls.receipt = json.loads((ROOT / "results" / "008_self_tuned_order.json").read_text())

    def test_saved_graphs_load_and_route_every_return_through_a_gate(self):
        paths = sorted((ROOT / "workflows").glob("008_*.json"))
        self.assertEqual(len(paths), 5)
        for p in paths:
            g = json.loads(p.read_text())
            lab.instantiate(g, self.up)
            direct = [e for e in g["edges"] if e["from_node_id"] in lab.UNITS and e["to_node_id"] == 2]
            self.assertEqual(direct, [], p.name)
            for u in lab.UNITS:
                self.assertTrue(any(e["from_node_id"] == lab.GATES[u] and e["to_node_id"] == 2
                                    and e["to_port"] == lab.WRITE[u] for e in g["edges"]), p.name)

    def test_units_are_the_005b_units(self):
        g = lab.build_graph(lab.W_005B)
        cfg = {n["id"]: n["config"] for n in g["nodes"]}
        for u, decay in zip(lab.UNITS, (.86, .95, .93)):
            self.assertAlmostEqual(cfg[u]["decay"], decay)
            self.assertAlmostEqual(cfg[u]["arm_threshold"], lab.CAL[str(u)]["arm_threshold"])

    def test_pairs_are_disjoint_and_matched(self):
        tr, te = lab.make_pairs()
        self.assertEqual((len(tr), len(te)), (16, 48))
        self.assertFalse({(j, g) for j, g, _ in tr} & {(j, g) for j, g, _ in te})

    def test_frozen_gates_do_not_move_and_live_gates_do(self):
        trial = (0, 32, 1.0)
        frozen = lab.simulate(lab.lab005.prepare_trial(lab.build_graph(lab.W_005B, 0), "AB", trial), self.up, 400)
        live = lab.simulate(lab.lab005.prepare_trial(lab.build_graph(lab.W_005B, 1), "AB", trial), self.up, 400)
        self.assertEqual(frozen["final_weights"], list(lab.W_005B))
        self.assertNotEqual(live["final_weights"], list(lab.W_005B))

    def test_receipt_supports_the_reported_negative_result(self):
        c = self.receipt["conditions"]
        acc = lambda n: c[n]["scores"]["650"]["all_six"]["correct"]
        self.assertEqual(c["passive"]["scores"]["650"]["all_six"]["of"], 96)
        self.assertLess(acc("self_tuned_frozen"), acc("fixed_005b"))
        self.assertLess(self.receipt["paired_tests_primary"]["self_tuned_frozen_vs_fixed_005b"]["p_two_sided"], 0.05)
        self.assertEqual(acc("passive"), 48)
        self.assertEqual(sum(v["clipped_frames"] for v in c.values()), 0)


if __name__ == "__main__":
    unittest.main()
