"""005b: keep exploratory third-unit graphs matched and physically connected."""
import importlib.util
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

class Test005b(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream=ROOT/"PerceptionLab"
        if not (cls.upstream/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("Missing upstream PerceptionLab/")

    def graphs(self,mode):
        suffix="" if mode=="feedback" else "_"+mode
        return {k:json.loads((ROOT/"workflows"/f"005_ABC093_{k}{suffix}.json").read_text())
                for k in ("AB","BA")}

    def test_equal_stimulus_injections_except_order(self):
        for mode in ("feedback","no_C","passive"):
            g=self.graphs(mode)
            self.assertEqual(g["AB"]["edges"],g["BA"]["edges"])
            ab=[n for n in g["AB"]["nodes"] if n["id"]<=1]
            ba=[n for n in g["BA"]["nodes"] if n["id"]<=1]
            self.assertEqual([x["config"]["warmup"] for x in ab],[40,72])
            self.assertEqual([x["config"]["warmup"] for x in ba],[72,40])
            for a,b in zip(ab,ba):
                x=a["config"].copy();y=b["config"].copy()
                del x["warmup"];del y["warmup"]
                self.assertEqual(x,y)

    def test_three_active_nodes_real_ports_and_calibration(self):
        src=ROOT/"experiments"/"005_order_of_falls"/"run.py"
        spec=importlib.util.spec_from_file_location("lab005_checker",src)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for mode in ("feedback","no_C","passive"):
            for order,g in self.graphs(mode).items():
                with self.subTest(mode=mode,order=order):
                    units=m.instantiate(g,self.upstream)
                    self.assertEqual(units[2].field.shape,(96,96))
                    self.assertAlmostEqual(units[5].decay,.93)
                    self.assertAlmostEqual(units[5].arm_threshold,.06781459787754025)
                    self.assertAlmostEqual(units[5].release_threshold,.030139821278906784)
                    returns={e["from_node_id"] for e in g["edges"]
                             if e["to_node_id"]==2 and e["from_port"]=="pulse"}
                    self.assertEqual(returns,{"feedback":{3,4,5},
                                              "no_C":{3,4},
                                              "passive":set()}[mode])

    def test_c_is_genuinely_active_with_feedback(self):
        src=ROOT/"experiments"/"005_order_of_falls"/"run.py"
        spec=importlib.util.spec_from_file_location("lab005_live",src)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for order,g in self.graphs("feedback").items():
            r=m.simulate(g,self.upstream,steps=260)
            self.assertTrue(any(t>=160 for t in r["spikes"]["5"]),
                            "Third unit must fire after external pulses end")
            self.assertEqual(r["clipped_frames"],0)

if __name__=="__main__":
    unittest.main()
