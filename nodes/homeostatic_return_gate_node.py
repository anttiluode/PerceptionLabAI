"""HomeostaticReturnGateNode — a return edge that tunes itself from its own firing rate (007).

The node sits between one unit's output pulse and the WaveField write port.
It keeps a running estimate of how often that unit fires and moves its own
gain toward a target rate:

    rate   <- rate + (spiked - rate) / rate_tau
    weight <- clip(weight + sign * learning_rate * (target_rate - rate), 0, 1)
    signal  = pre_spike * weight

Firing more often than the target lowers the return gain; firing less often
raises it. The only input is the unit's own pulse. There is no reward port,
no label, no reader and no view of any other unit.

`sign` is +1 for the homeostatic rule and -1 for the anti-homeostatic control.
With `learn_enabled = 0` it is a fixed gain with the same one-frame delay.

Homeostatic regulation of firing rate is a long-established idea in
neuroscience (synaptic scaling / intrinsic plasticity). This node is a minimal
test component for experiment 007, NOT a biological model and NOT a claim of
a new mechanism.

PerceptionLabAI 007, 15 November 2026, written by Claude Fable 5.2. MIT.
"""
import math
import __main__
import numpy as np
import cv2

BaseNode = __main__.BaseNode
QtGui = __main__.QtGui


class HomeostaticReturnGateNode(BaseNode):
    NODE_CATEGORY = "Cognition"
    NODE_COLOR = QtGui.QColor(70, 120, 135)

    def __init__(self):
        super().__init__()
        self.node_title = "Homeostatic Return"
        self.inputs = {"pre_spike": "signal"}
        self.outputs = {
            "signal": "signal",
            "weight": "signal",
            "rate": "signal",
            "rate_over_target": "signal",
            "last_update": "signal",
        }
        self.weight = 1.0
        self.target_rate = 0.010      # pulses per frame; 0.010 = one per 100 frames
        self.learning_rate = 0.02
        self.rate_tau = 200.0         # frames in the running rate estimate
        self.sign = 1.0               # +1 homeostatic, -1 anti-homeostatic control
        self.learn_enabled = 1
        self.rate = 0.0
        self.signal = 0.0
        self.last_update = 0.0
        self.rate_over_target = 0.0
        self.history = []
        self.display_img = np.zeros((120, 310, 3), np.uint8)

    @staticmethod
    def _clip(w):
        return min(1.0, max(0.0, float(w)))

    def step(self):
        inp = self.get_blended_input("pre_spike", "sum")
        pre = float(inp) if inp is not None else 0.0
        if not math.isfinite(pre):
            pre = 0.0
        spiked = 1.0 if abs(pre) > 1e-12 else 0.0

        tau = max(1.0, float(self.rate_tau))
        self.rate += (spiked - self.rate) / tau

        self.last_update = 0.0
        if int(self.learn_enabled):
            before = self.weight
            direction = 1.0 if float(self.sign) >= 0 else -1.0
            self.weight = self._clip(
                self.weight + direction * float(self.learning_rate)
                * (float(self.target_rate) - self.rate))
            self.last_update = self.weight - before

        self.signal = pre * self.weight
        self.rate_over_target = (self.rate / self.target_rate
                                 if self.target_rate > 1e-12 else 0.0)
        self.history.append(self.weight)
        self.history = self.history[-300:]
        self._render()

    def _render(self):
        im = np.zeros((120, 310, 3), np.uint8)
        cv2.putText(im, "HOMEOSTATIC RETURN", (5, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, .44, (225, 230, 235), 1)
        cv2.putText(im, "w=%.4f  learn=%d" % (self.weight, int(self.learn_enabled)),
                    (5, 39), cv2.FONT_HERSHEY_SIMPLEX, .40, (130, 245, 200), 1)
        cv2.putText(im, "rate/target=%.2f" % self.rate_over_target,
                    (5, 56), cv2.FONT_HERSHEY_SIMPLEX, .40, (190, 190, 230), 1)
        if len(self.history) > 1:
            last = None
            for j, w in enumerate(self.history):
                xy = (int(5 + 300 * j / (len(self.history) - 1)), int(112 - 40 * w))
                if last is not None:
                    cv2.line(im, last, xy, (115, 210, 240), 1)
                last = xy
        self.display_img = np.ascontiguousarray(im)

    def get_output(self, name):
        if name not in self.outputs:
            return None
        return float(getattr(self, name))

    def get_display_image(self):
        h, w = self.display_img.shape[:2]
        return QtGui.QImage(self.display_img.data, w, h, w * 3,
                            QtGui.QImage.Format.Format_BGR888)

    def get_config_options(self):
        return [
            ("Return weight (0..1)", "weight", self.weight, "float"),
            ("Target rate (pulses/frame)", "target_rate", self.target_rate, "float"),
            ("Learning rate", "learning_rate", self.learning_rate, "float"),
            ("Rate window (frames)", "rate_tau", self.rate_tau, "float"),
            ("Sign (+1 homeostatic, -1 control)", "sign", self.sign, "float"),
            ("Enable learning (1/0)", "learn_enabled", self.learn_enabled, None),
        ]

    def set_config_options(self, options):
        if "weight" in options:
            self.weight = self._clip(options["weight"])
        for field in ("target_rate", "learning_rate", "rate_tau", "sign"):
            if field in options:
                setattr(self, field, float(options[field]))
        if "learn_enabled" in options:
            self.learn_enabled = int(float(options["learn_enabled"]))
