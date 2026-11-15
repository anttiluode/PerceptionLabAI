"""Read-only learned linear probe of three fading-history units.

No teacher input, no connection back to the field. A separate held-out
training script supplies six fixed weights and a bias if the experiment
succeeds. The spike EMAs are internal readout memory, explicitly disclosed.
The causal medium is NEVER updated by this observer.
"""
import __main__
import math
import cv2
import numpy as np

BaseNode=__main__.BaseNode
QtGui=__main__.QtGui

class PopulationOrderReadoutNode(BaseNode):
    NODE_CATEGORY="Analysis"
    NODE_COLOR=QtGui.QColor(105,110,155)
    def __init__(self):
        super().__init__()
        self.node_title="Population Order Readout (frozen probe)"
        self.inputs={f"trace_{i}":"signal" for i in range(3)}
        self.inputs.update({f"spike_{i}":"signal" for i in range(3)})
        self.outputs={k:"signal" for k in ("score","decision","ready","spike_memory_0","spike_memory_1","spike_memory_2")}
        self.spike_decay=.92
        self.start_frame=180
        self.weights=[0.0]*6
        self.bias=0.0
        self.epoch=0
        self.spike_memory=np.zeros(3,dtype=float)
        self.features=[0.0]*6
        self.score=0.0
        self.decision=0.0
        self.ready=0.0
        self.display_img=np.zeros((124,300,3),np.uint8)
        self.score_hist=[]

    def step(self):
        self.epoch+=1
        traces=[]
        for i in range(3):
            x=self.get_blended_input(f"trace_{i}","sum")
            traces.append(float(x) if x is not None and math.isfinite(float(x)) else 0.0)
            spike=self.get_blended_input(f"spike_{i}","sum")
            spike=float(spike) if spike is not None and math.isfinite(float(spike)) else 0.0
            self.spike_memory[i]=self.spike_decay*self.spike_memory[i]+(1-self.spike_decay)*(1 if spike>0 else 0)
        x=traces+list(map(float,self.spike_memory))
        self.features=list(x)  # precise post-step features used in training
        self.score=float(self.bias+sum(w*v for w,v in zip(self.weights,x)))
        model_loaded=(any(abs(w)>1e-12 for w in self.weights))
        self.ready=1.0 if (self.epoch>=self.start_frame and model_loaded) else 0.0
        self.decision=(1.0 if self.score>=0 else -1.0) if self.ready else 0.0
        self.score_hist.append(self.score if self.ready else 0.0)
        self.score_hist=self.score_hist[-220:]
        self._render()

    def _render(self):
        im=np.zeros((124,300,3),np.uint8)
        cv2.putText(im,"ORDER PROBE (no teacher input)",(5,17),
                    cv2.FONT_HERSHEY_SIMPLEX,.40,(210,215,240),1)
        cv2.putText(im,"score=%+.3g  ready=%d"%(self.score,int(self.ready)),(5,36),
                    cv2.FONT_HERSHEY_SIMPLEX,.42,(145,255,160),1)
        cv2.putText(im,"AB if score>=0, else BA",(5,54),
                    cv2.FONT_HERSHEY_SIMPLEX,.38,(180,180,180),1)
        if len(self.score_hist)>1:
            den=max(1e-4,max(abs(v) for v in self.score_hist))
            last=None
            for j,v in enumerate(self.score_hist):
                xy=(int(j*296/(len(self.score_hist)-1))+2,
                    int(93-26*v/den))
                if last:cv2.line(im,last,xy,(85,220,230),1)
                last=xy
        cv2.line(im,(3,93),(297,93),(80,80,80),1)
        self.display_img=np.ascontiguousarray(im)

    def get_display_image(self):
        h,w=self.display_img.shape[:2]
        return QtGui.QImage(self.display_img.data,w,h,w*3,
                            QtGui.QImage.Format.Format_BGR888)

    def get_output(self,port_name):
        if port_name.startswith("spike_memory_"):
            try:return float(self.spike_memory[int(port_name[-1])])
            except (ValueError,IndexError):return 0.0
        if port_name in self.outputs:
            return float(getattr(self,port_name))
        return None

    def get_config_options(self):
        opts=[("Spike memory decay","spike_decay",self.spike_decay,"float"),
              ("Show after frame","start_frame",self.start_frame,None),
              ("Bias","bias",self.bias,"float")]
        for i,w in enumerate(self.weights):
            opts.append((f"Weight {i}","w"+str(i),w,"float"))
        return opts

    def set_config_options(self,options):
        if "spike_decay" in options:self.spike_decay=float(options["spike_decay"])
        if "start_frame" in options:self.start_frame=int(float(options["start_frame"]))
        if "bias" in options:self.bias=float(options["bias"])
        for i in range(6):
            if "w"+str(i) in options:self.weights[i]=float(options["w"+str(i)])
