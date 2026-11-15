"""006: ensure plastic edge is a *real* connection and reward changes node state."""
import importlib.util
import json
import pathlib
import sys
import unittest
import math

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

spec=importlib.util.spec_from_file_location(
    "run006",ROOT/"experiments"/"006_reward_selected_return"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

class Test006(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream=ROOT/"PerceptionLab"
        if not (cls.upstream/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("Clone main PerceptionLab into PerceptionLab/")

    def test_ab_ba_graphs_only_differ_in_input_timing(self):
        for kind in ("plastic","pruned"):
            ab=lab.base_graph("AB",kind);ba=lab.base_graph("BA",kind)
            self.assertEqual(ab["edges"],ba["edges"])
            for a,b in zip(ab["nodes"],ba["nodes"]):
                aa=a.copy();bb=b.copy()
                aa["config"]=aa["config"].copy()
                bb["config"]=bb["config"].copy()
                if a["id"] in (0,1):
                    aa["config"].pop("warmup");bb["config"].pop("warmup")
                self.assertEqual(aa,bb)
            self.assertEqual([n["config"]["warmup"] for n in ab["nodes"][:2]],[40,72])
            self.assertEqual([n["config"]["warmup"] for n in ba["nodes"][:2]],[72,40])

    def test_real_host_ports_through_plastic_node_and_wave_size(self):
        for kind in ("plastic","pruned"):
            graph=lab.base_graph("AB",kind)
            obj=lab.instantiate(graph,self.upstream)
            self.assertEqual(obj[2].field.shape,(96,96))
            self.assertEqual(obj[7].inputs["pre_spike"],"signal")
            self.assertEqual(obj[7].outputs["signal"],"signal")
            self.assertTrue(any(e["from_node_id"]==5 and
                                e["to_node_id"]==7 and
                                e["from_port"]=="pulse" for e in graph["edges"]))
            self.assertTrue(any(e["from_node_id"]==7 and
                                e["to_node_id"]==2 and
                                e["to_port"]=="write_4" for e in graph["edges"]))
            self.assertFalse(any(e["from_node_id"]==5 and
                                 e["to_node_id"]==2 for e in graph["edges"]))

    def test_reward_input_physically_updates_stored_weight(self):
        trainer=lab.make_trainer()
        trainer._render=lambda *args:None
        self.assertEqual(trainer.weight,.5)
        trainer.pre_step()
        trainer.set_input("reward_difference",.2,"signal",1)
        trainer.step()
        self.assertAlmostEqual(trainer.weight,.62)
        self.assertEqual(trainer.update_count,1)
        # Silence does not cause another update
        trainer.pre_step();trainer.step()
        self.assertAlmostEqual(trainer.weight,.62)
        # Negative reward reduces weight
        trainer.pre_step()
        trainer.set_input("reward_difference",-.3,"signal",1)
        trainer.step()
        self.assertAlmostEqual(trainer.weight,.44)
        self.assertEqual(trainer.update_count,2)

    def test_pruning_stops_physical_C_drive_not_C_spikes(self):
        graph=lab.trial_graph("AB",(0,32,1.),0.)
        res=lab.simulate(graph,self.upstream,steps=200)
        self.assertTrue(res["spikes"]["5"],"C should still respond")
        self.assertEqual(res["gate_effective_weight"],0.)
        self.assertEqual(res["sampled_clipped_frames"],0)

    def test_matched_trial_parameters_preserve_pulse_energy(self):
        trial=(-2,33,1.05)
        ab=lab.trial_graph("AB",trial,.5)
        ba=lab.trial_graph("BA",trial,.5)
        a=[n["config"] for n in ab["nodes"] if n["id"] in (0,1)]
        b=[n["config"] for n in ba["nodes"] if n["id"] in (0,1)]
        self.assertEqual(sorted(x["warmup"] for x in a),
                         sorted(x["warmup"] for x in b))
        self.assertEqual([x["amplitude"] for x in a],[x["amplitude"] for x in b])
        self.assertEqual(a[0]["width"],b[0]["width"])

if __name__=="__main__":
    unittest.main()
