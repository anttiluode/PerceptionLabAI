"""GrowingReturnNode — one unit's set of return branches, grown and pruned by local traffic (009).

A unit's pulse can be written back into the WaveField at up to eight sites.
Each branch has a weight. The weights share a fixed budget, so one branch can
only grow at the expense of the others, and a branch that falls below a
threshold is pruned for good.

Per frame, for each candidate site s:

    e_s <- trace_decay * e_s + (1 - trace_decay) * |site_s|        (recent activity at the branch tip)

When the unit fires:

    p_s  = e_s / sum(e)                                             (where has the field been busy lately?)
    w_s <- w_s + learning_rate * (p_s - mean(p over living branches))
    w   <- clip at 0, prune below prune_threshold, rescale living branches to `budget`

Output on every frame: out_s = pre_spike * w_s.

Everything the rule uses is local to the node: its own unit's pulse and the
field value at each branch tip. There is no reward, label or reader.

The ingredients are old: Hebbian growth toward recently active targets,
budget competition (synaptic scaling / Physarum-style conductance adaptation)
and pruning. This is a test component for experiment 009, NOT a biological
model of a dendrite or a vine.

PerceptionLabAI 009, 15 November 2026, written by Claude Fable 5.2. MIT.
"""
import math
import __main__
import numpy as np
import cv2

BaseNode = __main__.BaseNode
QtGui = __main__.QtGui

N_SITES = 8


class GrowingReturnNode(BaseNode):
    NODE_CATEGORY = "Cognition"
    NODE_COLOR = QtGui.QColor(88, 128, 70)

    def __init__(self):
        super().__init__()
        self.node_title = "Growing Return"
        self.inputs = {"pre_spike": "signal"}
        for s in range(N_SITES):
            self.inputs["site_%d" % s] = "signal"
        self.outputs = {"living_branches": "signal", "largest_weight": "signal"}
        for s in range(N_SITES):
            self.outputs["out_%d" % s] = "signal"
            self.outputs["w_%d" % s] = "signal"
        self.budget = 1.0
        self.learning_rate = 0.05
        self.trace_decay = 0.97
        self.prune_threshold = 0.02
        self.learn_enabled = 1
        self.weights = [self.budget / N_SITES] * N_SITES
        self.alive = [1] * N_SITES
        self.site_trace = [0.0] * N_SITES
        self.out = [0.0] * N_SITES
        self.update_count = 0
        self.display_img = np.zeros((120, 310, 3), np.uint8)

    def _renormalise(self):
        w = np.maximum(0.0, np.asarray(self.weights, dtype=float)) * np.asarray(self.alive, dtype=float)
        total = float(w.sum())
        if total > 1e-12:
            w *= float(self.budget) / total
        self.weights = [float(x) for x in w]

    def step(self):
        inp = self.get_blended_input("pre_spike", "sum")
        pre = float(inp) if inp is not None else 0.0
        if not math.isfinite(pre):
            pre = 0.0
        d = min(0.9999, max(0.0, float(self.trace_decay)))
        for s in range(N_SITES):
            v = self.get_blended_input("site_%d" % s, "sum")
            v = abs(float(v)) if v is not None and math.isfinite(float(v)) else 0.0
            self.site_trace[s] = d * self.site_trace[s] + (1.0 - d) * v

        if abs(pre) > 1e-12 and int(self.learn_enabled):
            e = np.asarray(self.site_trace, dtype=float)
            alive = np.asarray(self.alive, dtype=float)
            tot = float((e * alive).sum())
            if tot > 1e-12 and alive.sum() > 1:
                p = e * alive / tot
                mean_p = float(p.sum() / alive.sum())
                w = np.asarray(self.weights, dtype=float) + float(self.learning_rate) * (p - mean_p) * alive
                w = np.maximum(0.0, w)
                dead = (w < float(self.prune_threshold)) & (alive > 0)
                if dead.sum() < alive.sum():          # never prune the last branches all at once
                    alive[dead] = 0.0
                self.alive = [int(a) for a in alive]
                self.weights = [float(x) for x in w]
                self._renormalise()
                self.update_count += 1

        self.out = [pre * self.weights[s] for s in range(N_SITES)]
        self._render()

    def _render(self):
        im = np.zeros((120, 310, 3), np.uint8)
        cv2.putText(im, "GROWING RETURN  branches=%d" % int(sum(self.alive)), (5, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, .42, (225, 230, 235), 1)
        top = max(1e-9, max(self.weights))
        for s in range(N_SITES):
            x0 = 10 + s * 37
            h = int(80 * self.weights[s] / top)
            col = (90, 200, 120) if self.alive[s] else (60, 60, 60)
            cv2.rectangle(im, (x0, 110 - h), (x0 + 28, 110), col, -1 if self.alive[s] else 1)
            cv2.putText(im, str(s), (x0 + 9, 119), cv2.FONT_HERSHEY_SIMPLEX, .32, (200, 200, 200), 1)
        self.display_img = np.ascontiguousarray(im)

    def get_output(self, name):
        if name == "living_branches":
            return float(sum(self.alive))
        if name == "largest_weight":
            return float(max(self.weights))
        if name.startswith("out_"):
            return float(self.out[int(name[4:])])
        if name.startswith("w_"):
            return float(self.weights[int(name[2:])])
        return None

    def get_display_image(self):
        h, w = self.display_img.shape[:2]
        return QtGui.QImage(self.display_img.data, w, h, w * 3, QtGui.QImage.Format.Format_BGR888)

    def get_config_options(self):
        opts = [("Budget (sum of weights)", "budget", self.budget, "float"),
                ("Learning rate", "learning_rate", self.learning_rate, "float"),
                ("Site trace decay", "trace_decay", self.trace_decay, "float"),
                ("Prune threshold", "prune_threshold", self.prune_threshold, "float"),
                ("Enable growth (1/0)", "learn_enabled", self.learn_enabled, None)]
        for s in range(N_SITES):
            opts.append(("Weight to site %d" % s, "w%d" % s, self.weights[s], "float"))
        return opts

    def set_config_options(self, options):
        for f in ("budget", "learning_rate", "trace_decay", "prune_threshold"):
            if f in options:
                setattr(self, f, float(options[f]))
        if "learn_enabled" in options:
            self.learn_enabled = int(float(options["learn_enabled"]))
        if "weights" in options:
            self.weights = [float(x) for x in options["weights"]][:N_SITES]
        for s in range(N_SITES):
            if "w%d" % s in options:
                self.weights[s] = float(options["w%d" % s])
        if "alive" in options:
            self.alive = [int(a) for a in options["alive"]][:N_SITES]
