"""Experiment 003 source-node tests and upstream port compatibility."""
import json
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tests"))
from host_shim import load
Fade = load(ROOT/"nodes"/"fading_history_spike_node.py",
            "FadingHistorySpikeNode")

def feed(node,x):
    node.pre_step()
    node.set_input("signal_in",x)
    node.step()

class FadingPulseTests(unittest.TestCase):
    def test_silent_unit_never_fires(self):
        n = Fade(decay=.80,arm_threshold=.15,release_threshold=.08)
        for _ in range(200):
            feed(n,0)
        self.assertEqual(n.fire_count,0)
        self.assertEqual(n.get_output("pulse"),0)

    def test_one_burst_then_fade_fires_once(self):
        n = Fade(decay=.70,arm_threshold=.2,release_threshold=.08)
        for _ in range(12):
            feed(n,1)
        self.assertTrue(n.armed)
        spikes=[]
        for t in range(100):
            feed(n,0)
            if n.pulse:spikes.append(t)
        self.assertEqual(len(spikes),1)
        self.assertEqual(n.fire_count,1)

    def test_sustained_activity_holds_armed_without_pulse(self):
        n = Fade(decay=.7,arm_threshold=.2,release_threshold=.08)
        for _ in range(100):
            feed(n,1)
        self.assertTrue(n.armed)
        self.assertEqual(n.fire_count,0)

    def test_disabled_never_produces_a_pulse(self):
        n = Fade(decay=.7,arm_threshold=.2,release_threshold=.08,enabled=False)
        for x in [1.0]*20 + [0.0]*100 + [1.0]*20 + [0.0]*100:
            feed(n,x)
        self.assertEqual(n.fire_count,0)

    def test_inert_feedback_graph_has_no_spontaneous_activity(self):
        upstream=ROOT/"PerceptionLab"
        if not (upstream/"nodes"/"wavefieldnode.py").exists():
            self.skipTest("Check out upstream under PerceptionLab/")
        from importlib.util import spec_from_file_location,module_from_spec
        path=ROOT/"experiments"/"003_fade_closed_loop"/"run.py"
        spec=spec_from_file_location("fade_runner",path)
        mod=module_from_spec(spec)
        spec.loader.exec_module(mod)
        m=mod.classes(upstream)
        cal=mod.instruments(m,size=64,read=1,speed=.5,damping=.006,decay=.9,steps=125)
        no_boot=mod.one_run(m,cal,size=64,steps=170,feedback=True,
                            bootstrap=False,read=1)
        self.assertEqual(no_boot["total_spikes"],0)

    def test_workflow_matches_open_loop_calibration(self):
        graph=json.loads((ROOT/"workflows"/"003_fading_feedback_wave.json").read_text())
        n=next(x for x in graph["nodes"] if x["class_name"]=="FadingHistorySpikeNode")
        self.assertAlmostEqual(n["config"]["arm_threshold"],.72201012,places=5)
        self.assertAlmostEqual(n["config"]["release_threshold"],.320893387,places=5)

    def test_graph_ports_are_real_and_have_matching_types(self):
        upstream=ROOT/"PerceptionLab"/"nodes"
        if not upstream.exists():
            self.skipTest("Check out upstream under PerceptionLab/")
        graph=json.loads((ROOT/"workflows"/"003_fading_feedback_wave.json").read_text())
        mapping={"PulseSourceNode":"pulsesourcenode.py",
                 "WaveFieldNode":"wavefieldnode.py",
                 "TemporalMultiScopeNode":"temporalmultiscopenode.py",
                 "SignalPlotterNode":"signalplotternode.py"}
        objects={}
        for item in graph["nodes"]:
            klass=item["class_name"]
            C=Fade if klass=="FadingHistorySpikeNode" else load(
              upstream/mapping[klass],klass)
            objects[item["id"]]=C()
        self.assertEqual(len(objects),len(graph["nodes"]))
        for edge in graph["edges"]:
            a=objects[edge["from_node_id"]]
            b=objects[edge["to_node_id"]]
            self.assertIn(edge["from_port"],a.outputs)
            self.assertIn(edge["to_port"],b.inputs)
            self.assertEqual(a.outputs[edge["from_port"]],
                             b.inputs[edge["to_port"]])
        src=next(x for x in graph["nodes"] if x["class_name"]=="PulseSourceNode")
        self.assertEqual(src["config"]["period"],0)
        self.assertTrue(any(e["from_port"]=="pulse" and e["to_port"]=="write_0"
                            for e in graph["edges"]))

if __name__=="__main__":
    unittest.main()
