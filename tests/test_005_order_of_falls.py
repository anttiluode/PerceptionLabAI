"""Unit checks: matched sequence energy, host graph edges, and no label leakage."""
import copy
import importlib.util
import json
import pathlib
import sys
import unittest
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load
src=ROOT/"experiments"/"005_order_of_falls"/"run.py"
spec=importlib.util.spec_from_file_location("experiment_005",src)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Test005(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream=ROOT/"PerceptionLab"
        if not (cls.upstream/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("Clone upstream into PerceptionLab/")

    def test_order_changes_only_pulse_schedule(self):
        a=mod.read_graph("feedback","AB")
        b=mod.read_graph("feedback","BA")
        self.assertEqual(a["edges"],b["edges"])
        for x,y in zip(a["nodes"],b["nodes"]):
            if x["id"] in (0,1):
                p=x["config"].copy();q=y["config"].copy()
                p.pop("warmup");q.pop("warmup")
                self.assertEqual(p,q)
            else:
                self.assertEqual(x,y)
        self.assertEqual([a["nodes"][i]["config"]["warmup"] for i in (0,1)],[40,72])
        self.assertEqual([b["nodes"][i]["config"]["warmup"] for i in (0,1)],[72,40])

    def test_paired_trials_have_equal_source_energy(self):
        pair=(-2,36,1.08)
        a=mod.prepare_trial(mod.read_graph("feedback","AB"),"AB",pair)
        b=mod.prepare_trial(mod.read_graph("feedback","BA"),"BA",pair)
        na=[x for x in a["nodes"] if x["id"]<=1]
        nb=[x for x in b["nodes"] if x["id"]<=1]
        self.assertEqual(sorted(x["config"]["warmup"] for x in na),
                         sorted(x["config"]["warmup"] for x in nb))
        self.assertEqual([x["config"]["amplitude"] for x in na],
                         [x["config"]["amplitude"] for x in nb])
        self.assertEqual(na[0]["config"]["warmup"],na[1]["config"]["warmup"]-36)
        self.assertEqual(nb[1]["config"]["warmup"],nb[0]["config"]["warmup"]-36)

    def test_all_saved_variants_host_load_ports_and_size(self):
        for name in ("feedback","passive","no_C"):
            for order in ("AB","BA"):
                with self.subTest(mode=name,order=order):
                    g=mod.read_graph(name,order)
                    objects=mod.instantiate(g,self.upstream)
                    self.assertEqual(objects[2].field.shape,(96,96))
                    self.assertEqual(len([n for n in g["nodes"]
                        if n["class_name"]=="FadingHistorySpikeNode"]),3)
        empty=json.loads((ROOT/"workflows"/"005_no_stimulus.json").read_text())
        self.assertEqual(mod.instantiate(empty,self.upstream)[2].field.shape,(96,96))

    def test_passive_disconnects_every_return(self):
        for order in ("AB","BA"):
            g=mod.read_graph("passive",order)
            self.assertFalse(any(e["from_node_id"] in (3,4,5) and
                e["to_node_id"]==2 for e in g["edges"]))
            g2=mod.read_graph("feedback",order)
            self.assertEqual(sum(e["from_node_id"] in (3,4,5) and
                e["to_node_id"]==2 for e in g2["edges"]),3)

    def test_readout_has_no_teacher_edge_and_does_not_write(self):
        g=mod.read_graph()
        r=mod.instantiate(g,self.upstream)[6]
        self.assertFalse(any("label" in k or "teacher" in k for k in r.inputs))
        self.assertFalse(any(e["from_node_id"]==6 and e["to_node_id"]==2
                             for e in g["edges"]))
        self.assertEqual(r.get_output("ready"),0.0)
        self.assertTrue(any(abs(v)>1e-8 for v in r.weights))
        self.assertEqual(r.start_frame,360)
        other=mod.instantiate(mod.read_graph("feedback","BA"),self.upstream)[6]
        self.assertEqual(r.weights,other.weights)
        passive=mod.instantiate(mod.read_graph("passive","AB"),self.upstream)[6]
        self.assertTrue(all(v==0 for v in passive.weights))
        self.assertTrue(all(name in r.inputs for name in
                             ("trace_0","trace_1","trace_2","spike_0","spike_1","spike_2")))

    def test_no_source_means_no_spikes(self):
        graph=json.loads((ROOT/"workflows"/"005_no_stimulus.json").read_text())
        sample=mod.simulate(graph,self.upstream,steps=95)
        self.assertEqual(sample["peak_energy"],0)
        self.assertTrue(all(not v for v in sample["spikes"].values()))

    def test_ridge_probe_uses_only_training_pairs(self):
        # Only a synthetic sanity check for probe score, NOT the physical result.
        train={}
        test={}
        for i in range(5):
            train[(i,"AB")]={"features":{160:[1+i*.01,0,0,0,0,0]}}
            train[(i,"BA")]={"features":{160:[-1+i*.01,0,0,0,0,0]}}
            test[(i,"AB")]={"features":{160:[1.01,0,0,0,0,0]}}
            test[(i,"BA")]={"features":{160:[-1.01,0,0,0,0,0]}}
        model=mod.fit_linear(train,160)
        score=mod.test_linear(test,model,160)
        self.assertEqual(score["balanced_accuracy"],1.0)
        self.assertEqual(score["both_orders_correct_pairs"],5)

if __name__=="__main__":
    unittest.main()
