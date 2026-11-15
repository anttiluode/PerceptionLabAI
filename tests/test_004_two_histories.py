"""004's saved workflow is the scientific object; verify node ports and controls."""
import copy
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load
from importlib.util import spec_from_file_location,module_from_spec

p=ROOT/"experiments"/"004_two_histories"/"run.py"
spec=spec_from_file_location("lab004",p)
lab004=module_from_spec(spec);spec.loader.exec_module(lab004)


class Test004(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream=ROOT/"PerceptionLab"
        if not (cls.upstream/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("clone PerceptionLab inside PerceptionLabAI")

    def test_all_workflows_have_real_ports(self):
        for path in (ROOT/"workflows").glob("004*.json"):
            with self.subTest(path=path):
                g=json.loads(path.read_text())
                obj=lab004.prepare(g,self.upstream)
                self.assertEqual(obj[1].field.shape,(96,96))
                self.assertEqual(len([n for n in g["nodes"]
                    if n["class_name"]=="FadingHistorySpikeNode"]),2)

    def test_both_units_share_the_same_wave(self):
        g=json.loads((ROOT/"workflows"/"004_two_fades_one_field.json").read_text())
        wave=[n for n in g["nodes"] if n["class_name"]=="WaveFieldNode"]
        self.assertEqual(len(wave),1)
        self.assertTrue(any(e["from_node_id"]==2 and e["to_node_id"]==1
                            and e["from_port"]=="pulse" for e in g["edges"]))
        self.assertTrue(any(e["from_node_id"]==3 and e["to_node_id"]==1
                            and e["from_port"]=="pulse" for e in g["edges"]))

    def test_swaps_change_only_intended_dimension(self):
        base=json.loads((ROOT/"workflows"/"004_two_fades_one_field.json").read_text())
        swapD=json.loads((ROOT/"workflows"/"004_swap_decay.json").read_text())
        swapS=json.loads((ROOT/"workflows"/"004_swap_sites.json").read_text())
        b={n["id"]:n for n in base["nodes"]}
        d={n["id"]:n for n in swapD["nodes"]}
        s={n["id"]:n for n in swapS["nodes"]}
        self.assertEqual(d[2]["config"]["decay"],b[3]["config"]["decay"])
        self.assertEqual(d[3]["config"]["decay"],b[2]["config"]["decay"])
        self.assertEqual(base["edges"],swapD["edges"])
        self.assertEqual(s[2]["config"]["decay"],b[2]["config"]["decay"])
        self.assertEqual(s[3]["config"]["decay"],b[3]["config"]["decay"])
        self.assertEqual(b[1]["config"],s[1]["config"])

    def test_separate_single_pulse_calibration_nonzero(self):
        g=json.loads((ROOT/"workflows"/"004_two_fades_one_field.json").read_text())
        cal=lab004.calibrate(self.upstream,g,steps=200)
        self.assertGreater(cal["trace_peaks"]["2"],0)
        self.assertGreater(cal["trace_peaks"]["3"],0)

    def test_no_seed_no_activity(self):
        g=json.loads((ROOT/"workflows"/"004_no_seed.json").read_text())
        cal=lab004.calibrate(self.upstream,json.loads(
           (ROOT/"workflows"/"004_two_fades_one_field.json").read_text()),200)
        r=lab004.run_case(self.upstream,g,cal,steps=120)
        self.assertEqual(r["total_spikes"],{"A":0,"B":0})
        self.assertEqual(r["energy"]["max_abs_field"],0)

    def test_single_shot_bootstrap_and_two_returns(self):
        g=json.loads((ROOT/"workflows"/"004_two_fades_one_field.json").read_text())
        source=next(n for n in g["nodes"] if n["id"]==0)["config"]
        self.assertEqual(source["period"],0)
        self.assertEqual(source["width"],2)
        self.assertTrue(0<source["amplitude"]<1)
        returns=[e for e in g["edges"] if e["to_node_id"]==1 and
                 e["from_port"]=="pulse"]
        self.assertEqual(len(returns),2)

if __name__=="__main__":
    unittest.main()
