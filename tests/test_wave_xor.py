import json
import math
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load
Gate=load(ROOT/"nodes"/"wave_arrival_gate_node.py","WaveArrivalGateNode")

class WaveXORTests(unittest.TestCase):
    def test_absolute_field_gate(self):
        gate=Gate(threshold=.15)
        for value,expected in [(0,0),(.149,0),(.15,1),(-.4,1),(0,0)]:
            gate.pre_step();gate.set_input("signal_in",value);gate.step()
            self.assertEqual(gate.get_output("gate"),expected)

    def test_existing_soma_xor_truth_table(self):
        path=ROOT/"PerceptionLab"/"nodes"/"resonatorsomanode.py"
        if not path.exists():self.skipTest("Missing upstream checkout")
        Soma=load(path,"ResonatorSomaNode")
        gate=Soma(gate="XOR")
        for a in (0,1):
            for b in (0,1):
                gate.pre_step()
                gate.set_input("in_a",a);gate.set_input("in_b",b)
                gate.step()
                self.assertEqual(gate.get_output("fire"),float(a^b))

    def test_saved_workflow_classes_ports(self):
        upstream=ROOT/"PerceptionLab"/"nodes"
        if not upstream.exists():self.skipTest("Missing upstream checkout")
        graph=json.loads((ROOT/"workflows"/"002_wavefield_resonator_xor.json").read_text())
        modules={"PulseSourceNode":"pulsesourcenode.py",
                 "WaveFieldNode":"wavefieldnode.py",
                 "ResonatorSomaNode":"resonatorsomanode.py",
                 "SignalPlotterNode":"signalplotternode.py"}
        built={}
        for desc in graph["nodes"]:
            name=desc["class_name"]
            C=Gate if name=="WaveArrivalGateNode" else load(upstream/modules[name],name)
            built[desc["id"]]=C()
        for edge in graph["edges"]:
            x=built[edge["from_node_id"]]
            y=built[edge["to_node_id"]]
            self.assertIn(edge["from_port"],x.outputs)
            self.assertIn(edge["to_port"],y.inputs)
            self.assertEqual(x.outputs[edge["from_port"]],y.inputs[edge["to_port"]])

    def test_one_case_no_pulse_is_silent_and_logic_exact(self):
        upstream=ROOT/"PerceptionLab"
        if not (upstream/"nodes"/"wavefieldnode.py").exists():
            self.skipTest("Missing upstream checkout")
        from importlib.util import spec_from_file_location, module_from_spec
        path=ROOT/"experiments"/"002_wave_xor"/"run.py"
        spec=spec_from_file_location("wave_xor_runner",path)
        mod=module_from_spec(spec);spec.loader.exec_module(mod)
        modules=mod.modules(upstream)
        peak_a=mod.single_peak(modules[0],modules[1],64,0,110)
        peak_b=mod.single_peak(modules[0],modules[1],64,1,110)
        self.assertGreater(peak_a,0);self.assertGreater(peak_b,0)
        thresholds=(.3*peak_a,.3*peak_b)
        case=mod.one_case(modules,64,thresholds,0,110,False,False)
        self.assertEqual(case["xor_active"],0)
        self.assertEqual(case["a_active"],0)
        self.assertEqual(case["b_active"],0)
        self.assertEqual(case["truth_table_mismatches"],0)


if __name__=="__main__":unittest.main()
