"""011 contract: independent histories, untouched reader split, and frozen structure."""
import importlib.util
import json
import pathlib
import sys
import unittest
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("lab011",ROOT/"experiments"/"011_dual_history"/"run.py")
lab=importlib.util.module_from_spec(spec)
sys.modules["lab011"]=lab
spec.loader.exec_module(lab)

class TestDesign(unittest.TestCase):
    def test_four_crossed_histories_and_disjoint_body_ids(self):
        ids,train,n_tr,n_te=lab.prepare_ids(False)
        self.assertEqual((n_tr,n_te),(8,16))
        combos=[(old,new) for old in lab.LABELS for new in lab.LABELS]
        self.assertEqual(combos,[("AB","AB"),("AB","BA"),("BA","AB"),("BA","BA")])
        self.assertEqual(len(train),8)
        self.assertEqual(len({x["id"] for x in ids if x["id"] not in train}),16)
        self.assertEqual(len([(i,o,n) for i in ids for o,n in combos]),96)
        # Independence: no first-history label predicts the second.
        for old in lab.LABELS:
            self.assertEqual([new for o,new in combos if o==old],["AB","BA"])

    def test_hardening_reuses_ten_experimental_parameters(self):
        self.assertEqual(lab.params_for("soft")["prune_threshold"],.02)
        self.assertEqual(lab.params_for("frozen"),lab.params_for("soft"))
        self.assertEqual(lab.params_for("age")["harden_mode"],2)
        self.assertEqual(lab.params_for("use")["harden_mode"],1)
        self.assertEqual(lab.params_for("age")["harden_rate"],.2)
        self.assertEqual(lab.params_for("use")["harden_rate"],.2)
        self.assertEqual(lab.CHECKPOINTS,(10,20))

    def test_new_label_is_unreadable_from_an_unchanged_structure(self):
        # Synthetic sanity test: the old state can reveal old but *cannot*
        # discriminate balanced new labels when structure remains identical.
        first={}
        for ident in range(6):
            for old in lab.LABELS:
                first[(ident,old)]=([1. if old=="AB" else -1.,0,0,0,0,0])
        training=[(v,o) for (j,o),v in first.items() if j<2]
        old_model=lab.fit(training)
        full={(j,o,n):first[(j,o)] for j in range(6)
              for o in lab.LABELS for n in lab.LABELS}
        new_model=lab.fit([(full[k],k[2]) for k in full if k[0]<2])
        score=lab.eval_both(old_model,new_model,{k:v for k,v in full.items() if k[0]>=2})
        self.assertEqual(score["old_accuracy"],1.0)
        self.assertEqual(score["new_accuracy"],0.5)
        self.assertEqual(score["joint_accuracy"],0.5)

    def test_frozen_reader_is_not_retrained_at_interference(self):
        samples=[([1.,0,0,0,0,0],"AB"),([-1.,0,0,0,0,0],"BA")]
        reader=lab.fit(samples)
        before=lab.score_features(reader,[1.,0,0,0,0,0])
        after=lab.score_features(reader,[-1.,0,0,0,0,0])
        self.assertGreater(before,0)
        self.assertLess(after,0)
        self.assertEqual(reader["n_training"],2)

    def test_metrics_include_joint_outcome_and_paired_comparisons(self):
        a={"per_body":{"1:AB:BA":{"old":True,"new":True,"both":True},
                       "2:BA:AB":{"old":True,"new":False,"both":False}}}
        b={"per_body":{"1:AB:BA":{"old":True,"new":False,"both":False},
                       "2:BA:AB":{"old":True,"new":True,"both":True}}}
        p=lab.paired(a,b,"both")
        self.assertEqual(p["first_only_correct"],1)
        self.assertEqual(p["second_only_correct"],1)
        self.assertEqual(p["two_sided_sign_p"],1.0)

    def test_readout_floor_is_same_as_009(self):
        a=[1e-3,-2e-2,3e-2,0,0.001,0.1]
        f=[0.01,0.01,0.01,0.001,0.001,0.001]
        self.assertEqual(lab.measured(a,f),[0.,-0.02,0.03,0.,.001,.1])

class TestRealHost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up=ROOT/"PerceptionLab"
        if not (cls.up/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("Clone upstream PerceptionLab/")

    def test_learning_disabled_preserves_weights_after_an_episode(self):
        import numpy as np
        c=lab.core
        cal=c.calibrate(self.up)
        st=c.uniform_structure()
        before=json.dumps(st,sort_keys=True)
        episode=c.episode(st,cal["thresholds"],self.up,"AB",
                          gap=32,scale=1.,steps=100,learn=0,
                          params=lab.params_for("soft"))
        saved=episode["structure"]
        self.assertEqual(saved["weights"],st["weights"])
        self.assertEqual(saved["alive"],st["alive"])
        self.assertTrue(all(not any(h) for h in saved["hardness"]))
        self.assertEqual(before,json.dumps(st,sort_keys=True))

    def test_probe_after_reset_uses_same_input_for_both_histories(self):
        c=lab.core
        cal=c.calibrate(self.up)
        st=c.uniform_structure()
        first=c.build_graph(st,cal["thresholds"],None,probe_site=lab.r9.PROBE_SITE,learn=0)
        second=c.build_graph(st,cal["thresholds"],None,probe_site=lab.r9.PROBE_SITE,learn=0)
        self.assertEqual(first,second)
        nodes=c.instantiate(first,self.up)
        self.assertEqual(nodes[2].field.shape,(96,96))
        self.assertEqual(sum(n["class_name"]=="GrowingReturnNode" for n in first["nodes"]),3)

if __name__=="__main__":
    unittest.main()
