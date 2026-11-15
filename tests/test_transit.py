import math
import pathlib
import random
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load
Reader=load(ROOT/"nodes"/"temporal_transit_predictor_node.py",
            "TemporalTransitPredictorNode")

def feed(node,a,b):
    node.pre_step()
    node.set_input("near",a)
    node.set_input("far",b)
    node.step()

class TransitTests(unittest.TestCase):
    def test_truly_delayed_signal(self):
        rng=random.Random(42)
        a=[rng.gauss(0,1) for _ in range(650)]
        d=9
        b=[0.0 if t<d else 0.65*a[t-d]+rng.gauss(0,.08)
           for t in range(len(a))]
        r=Reader(delay=d,window=160,min_samples=40)
        for x,y in zip(a,b): feed(r,x,y)
        self.assertEqual(r.valid,1.0)
        self.assertLess(r.mse_delayed,r.mse_simultaneous*0.1)
        self.assertGreater(r.advantage_db,10)

    def test_zero_delay_identical_control(self):
        rng=random.Random(4)
        r=Reader(delay=0,min_samples=20)
        for _ in range(250): feed(r,rng.random(),rng.random())
        self.assertEqual(r.valid,1.0)
        self.assertEqual(r.mse_delayed,r.mse_simultaneous)
        self.assertEqual(r.advantage_db,0.0)

    def test_flat_input_has_no_spurious_prediction(self):
        r=Reader(delay=5,min_samples=12)
        for _ in range(100): feed(r,1.0,0.1)
        self.assertEqual(r.valid,0.0)

    def test_changing_delay_resets_history(self):
        rng=random.Random(5)
        r=Reader(delay=2,min_samples=12)
        for _ in range(100): feed(r,rng.random(),rng.random())
        self.assertEqual(r.valid,1.0)
        r.set_config_options({"delay":6})
        self.assertEqual(r.valid,0)
        self.assertEqual(len(r._near),0)

    def test_real_upstream_wave_propagates(self):
        source=ROOT/"PerceptionLab"/"nodes"/"wavefieldnode.py"
        if not source.exists():
            self.skipTest("Check out upstream under PerceptionLab/")
        Wave=load(source,"WaveFieldNode")
        wave=Wave(size=96)
        tap0,tap1=[],[]
        for t in range(130):
            wave.pre_step()
            if t==4: wave.set_input("impulse",2.0)
            wave.step()
            tap0.append(wave.get_output("read_0"))
            tap1.append(wave.get_output("read_1"))
        self.assertGreater(max(map(abs,tap0)),0.0)
        self.assertGreater(max(map(abs,tap1)),0.0)
        self.assertNotEqual(tap0,tap1)
        self.assertTrue(all(math.isfinite(x) for x in tap0+tap1))

    def test_workflow_uses_existing_classes_and_real_ports(self):
        import json
        wf=json.loads((ROOT/"workflows"/"001_wave_transit_predictor.json").read_text())
        upstream=ROOT/"PerceptionLab"/"nodes"
        if not upstream.exists():
            self.skipTest("Check out upstream under PerceptionLab/")
        modules={
            "WaveFieldNode":"wavefieldnode.py",
            "PulseSourceNode":"pulsesourcenode.py",
            "TemporalMultiScopeNode":"temporalmultiscopenode.py",
            "SignalPlotterNode":"signalplotternode.py",
        }
        built={}
        for item in wf["nodes"]:
            klass=item["class_name"]
            if klass=="TemporalTransitPredictorNode":
                C=Reader
            else:
                C=load(upstream/modules[klass],klass)
            built[item["id"]]=C()
        for edge in wf["edges"]:
            sender=built[edge["from_node_id"]]
            receiver=built[edge["to_node_id"]]
            self.assertIn(edge["from_port"],sender.outputs)
            self.assertIn(edge["to_port"],receiver.inputs)
            self.assertEqual(sender.outputs[edge["from_port"]],
                             receiver.inputs[edge["to_port"]])


if __name__=="__main__":
    unittest.main()
