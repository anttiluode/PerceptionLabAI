"""Simulate PerceptionLab's REAL saved-graph construction and graph step order.

Regression for bug: 'size: 96' used to leave 256x256 wave arrays in the GUI.
Checkout upstream at a revision with the WaveField config-size fix (PR #4).
This is a host-compatible headless execution of real node source and saved
edge transfer order, NOT a PyQt interactive screenshot test.
"""
import copy
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

CLASS_FILES={
    "PulseSourceNode":"pulsesourcenode.py",
    "WaveFieldNode":"wavefieldnode.py",
    "SignalPlotterNode":"signalplotternode.py",
    "TemporalMultiScopeNode":"temporalmultiscopenode.py",
}

def prepare(upstream, disabled_feedback=False, bootstrap_amplitude=1.0):
    workflow=json.loads((ROOT/"workflows"/"003_fading_feedback_wave.json").read_text())
    units={}
    for definition in workflow["nodes"]:
        name=definition["class_name"]
        if name=="FadingHistorySpikeNode":
            file=ROOT/"nodes"/"fading_history_spike_node.py"
        else:
            file=upstream/"nodes"/CLASS_FILES[name]
        Class=load(file,name)
        unit=Class() # exact no-arg construction pattern in real GUI
        config=copy.deepcopy(definition["config"])
        if name=="PulseSourceNode":
            config["amplitude"]=bootstrap_amplitude
        if hasattr(unit,"set_config_options"):
            unit.set_config_options(config)
            # Simulate PerceptionLab GUI fallback for unset config attributes.
            for key,value in config.items():
                if hasattr(unit,key):
                    present=getattr(unit,key)
                    if present != value:
                        setattr(unit,key,value)
        else:
            for key,value in config.items():
                if hasattr(unit,key):
                    setattr(unit,key,value)
        units[definition["id"]]=unit
    edges=[
      edge for edge in workflow["edges"] if
      not (disabled_feedback and
           edge["from_port"]=="pulse" and edge["to_port"]=="write_0")
    ]
    return units,edges

def replay(upstream,steps=550,disabled_feedback=False,bootstrap_amplitude=1.0):
    units,edges=prepare(upstream,disabled_feedback,bootstrap_amplitude)
    field=units[1]
    if field.field.shape != (96,96) or field.vel.shape != (96,96):
        raise AssertionError(
          "GUI loader mismatch: saved size=%r, actual field=%r" %
          (field.size,field.field.shape))
    fired=[]
    for tick in range(steps):
        for node in units.values():
            node.pre_step()
        # Actual GUI host transfers *all previous-tick outputs* before ANY step.
        for edge in edges:
            source=units[edge["from_node_id"]]
            target=units[edge["to_node_id"]]
            value=source.get_output(edge["from_port"])
            if value is not None:
                target.set_input(edge["to_port"],value,"signal",
                                 edge.get("learned_weight",1.0))
        for node in units.values():
            node.step()
        if units[2].get_output("pulse")>0:
            fired.append(tick)
    return fired,units

class HostGraph003Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream=ROOT/"PerceptionLab"
        if not (cls.upstream/"nodes"/"wavefieldnode.py").exists():
            raise unittest.SkipTest("Checkout upstream at WaveField size patch")

    def test_real_loader_builds_calibrated_96_field(self):
        units,_=prepare(self.upstream)
        wave=units[1]
        self.assertEqual(wave.size,96)
        self.assertEqual(wave.field.shape,(96,96))
        self.assertAlmostEqual(wave.spacing_px,96*.72/7,places=4)

    def test_replay_with_saved_edges_regenerates_beats(self):
        fired,units=replay(self.upstream,550)
        self.assertGreaterEqual(len(fired),10)
        self.assertGreaterEqual(sum(t>=275 for t in fired),6)
        self.assertEqual(units[2].fire_count,len(fired))

    def test_replay_unplugged_does_not_regenerate(self):
        fired,_=replay(self.upstream,550,disabled_feedback=True)
        self.assertEqual(len(fired),1)

    def test_replay_without_seed_stays_silent(self):
        fired,_=replay(self.upstream,300,bootstrap_amplitude=0.0)
        self.assertEqual(fired,[])

if __name__=="__main__":
    unittest.main()
