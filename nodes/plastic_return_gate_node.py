"""PlasticReturnGateNode — one trainable physical return edge (006).

This node gates a *real* presynaptic pulse back into upstream WaveField.
A two-sided, reward-guided perturbation changes its own retained weight:

    w <- clip(w + learning_rate*(R_plus - R_minus)/(2*delta)
                  - learning_rate*resource_cost, 0, 1)

The two reward values are compared by an EXTERNAL training environment,
not autonomously generated inside the neuron. Reward *difference* enters
through a typed input; no AB/BA label, decoder weights or class names do.

This is task-directed, bounded synaptic selection / simple plasticity,
NOT Hebbian/STDP, not growth of an anatomical arbor, and not a claim of
biologically local learning. The GUI permits a reward source to be wired
to the update port; in 006 headless experiments the reward comparison is
sent between episodes, while w persists.

PerceptionLabAI 006, November 2026. MIT.
"""
import math
import __main__
import numpy as np
import cv2

BaseNode=__main__.BaseNode
QtGui=__main__.QtGui

class PlasticReturnGateNode(BaseNode):
    NODE_CATEGORY="Cognition"
    NODE_COLOR=QtGui.QColor(130,112,65)

    def __init__(self):
        super().__init__()
        self.node_title="Plastic Return / reward-selected C branch"
        self.inputs={"pre_spike":"signal","reward_difference":"signal"}
        self.outputs={
            "signal":"signal","weight":"signal","effective_weight":"signal",
            "update_count":"signal","last_update":"signal",
            "pre_activity":"signal"
        }
        self.weight=.50
        self.exploration_direction=0.0
        self.perturbation=.10
        self.learning_rate=.12
        self.resource_cost=.0
        self.learn_enabled=0
        self.signal=0.
        self.effective_weight=self.weight
        self.update_count=0
        self.last_update=0.
        self.pre_activity=0.
        self.history=[]
        self.display_img=np.zeros((120,310,3),np.uint8)

    def _clip(self,w):
        return min(1.,max(0.,float(w)))

    def step(self):
        reward=self.get_blended_input("reward_difference","sum")
        self.last_update=0.
        if reward is not None and self.learn_enabled:
            r=float(reward)
            if math.isfinite(r) and self.perturbation>1e-7:
                delta=self.learning_rate*(
                    r/(2.*self.perturbation)-self.resource_cost)
                before=self.weight
                self.weight=self._clip(self.weight+delta)
                self.last_update=self.weight-before
                self.update_count+=1
        inp=self.get_blended_input("pre_spike","sum")
        self.pre_activity=float(inp) if inp is not None else 0.
        if not math.isfinite(self.pre_activity):self.pre_activity=0.
        direction=max(-1.,min(1.,float(self.exploration_direction)))
        self.effective_weight=self._clip(self.weight+direction*self.perturbation)
        self.signal=self.pre_activity*self.effective_weight
        self.history.append(self.weight)
        self.history=self.history[-160:]
        self._render()

    def _render(self):
        im=np.zeros((120,310,3),np.uint8)
        cv2.putText(im,"BOUNDED PLASTIC RETURN", (5,17),
                    cv2.FONT_HERSHEY_SIMPLEX,.44,(225,230,235),1)
        cv2.putText(im,"w=%.4f  effective=%.4f"%(self.weight,self.effective_weight),
                    (5,39),cv2.FONT_HERSHEY_SIMPLEX,.40,(130,245,200),1)
        cv2.putText(im,"reward updates: %d"%self.update_count,
                    (5,56),cv2.FONT_HERSHEY_SIMPLEX,.40,(190,190,230),1)
        if len(self.history)>1:
            last=None
            for j,w in enumerate(self.history):
                xy=(int(5+300*j/(len(self.history)-1)),int(112-40*w))
                if last is not None:cv2.line(im,last,xy,(115,210,240),1)
                last=xy
        self.display_img=np.ascontiguousarray(im)

    def get_output(self,name):
        if name not in self.outputs:return None
        if name=="weight":return float(self.weight)
        return float(getattr(self,name))

    def get_display_image(self):
        h,w=self.display_img.shape[:2]
        return QtGui.QImage(self.display_img.data,w,h,w*3,QtGui.QImage.Format.Format_BGR888)

    def get_config_options(self):
        return [
            ("Retained weight","weight",self.weight,"float"),
            ("Exploration sign (-1,0,+1)","exploration_direction",
             self.exploration_direction,"float"),
            ("Perturbation","perturbation",self.perturbation,"float"),
            ("Learning rate","learning_rate",self.learning_rate,"float"),
            ("Resource cost","resource_cost",self.resource_cost,"float"),
            ("Enable reward updates (1/0)","learn_enabled",self.learn_enabled,None)
        ]

    def set_config_options(self,options):
        if "weight" in options:self.weight=self._clip(options["weight"])
        for field in ("exploration_direction","perturbation","learning_rate","resource_cost"):
            if field in options:setattr(self,field,float(options[field]))
        if "learn_enabled" in options:self.learn_enabled=int(float(options["learn_enabled"]))
        self.effective_weight=self._clip(self.weight+
            self.exploration_direction*self.perturbation)
