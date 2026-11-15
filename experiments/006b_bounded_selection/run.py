"""006b — lower-rate, capped, multi-context reward selection.

Separate *exploratory* extension after 006 failed; never overwrite 006.
The fixed probe is fitted on the original 006 readout-fit training split.
Feedback rewards use EIGHT DIFFERENT experiences, two per update.
Final evaluation uses EIGHT DIFFERENT, fresh AB/BA pairs that were NOT
used in 006 nor the 006b reward loop.

The training environment still knows AB/BA labels to calculate reward.
This tests a more conservative supervised update, NOT autonomous goals.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import pathlib
import statistics

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "original006",ROOT/"experiments"/"006_reward_selected_return"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

# 006's TRAIN pairs are used only to fit the frozen order observer.
# New experience and final examples are disjoint from the original 006.
EXPERIENCES=[
 (-6,31,.99),(4,36,1.11),(1,29,.89),(-3,44,1.07),
 (5,33,.95),(-1,47,1.03),(3,40,.91),(0,25,1.09)
]
FRESH_FINAL=[
 (-7,35,.91),(7,46,1.08),(-6,45,1.12),(6,25,.88),
 (-2,49,1.04),(2,47,.93),(1,30,1.13),(-1,26,.97)
]
MAX_UPDATE=.05
RATE=.02
def train_bounded(upstream,model,reverse=False):
    trainer=lab.make_trainer()
    trainer.learning_rate=RATE
    trainer.max_update=MAX_UPDATE
    trainer.resource_cost=0.0
    log=[{"step":-1,"weight":trainer.weight}]
    for j in range(0,len(EXPERIENCES),2):
        batch=EXPERIENCES[j:j+2]
        plus=[]
        minus=[]
        for trial in batch:
            p,_=lab.paired_utility(upstream,trial,trainer.weight,model,+1)
            m,_=lab.paired_utility(upstream,trial,trainer.weight,model,-1)
            plus.append(p);minus.append(m)
        reward_diff=statistics.mean(plus)-statistics.mean(minus)
        if reverse:reward_diff=-reward_diff
        before=trainer.weight
        trainer.pre_step()
        trainer.set_input("reward_difference",reward_diff,"signal",1.0)
        trainer.step()
        log.append({
            "step":j//2,
            "contexts":batch,
            "utility_plus_mean":statistics.mean(plus),
            "utility_minus_mean":statistics.mean(minus),
            "reward_diff_used":reward_diff,
            "weight_before":before,
            "weight_after":trainer.weight,
            "update":trainer.last_update,
            "max_update":MAX_UPDATE
        })
    return trainer.weight,log


def main(upstream):
    upstream=pathlib.Path(upstream)
    model,reader_train=lab.model_on_pruned(upstream)
    learned,log=train_bounded(upstream,model,False)
    reversed_weight,reverse_log=train_bounded(upstream,model,True)
    conditions={
        "bounded_learned":learned,
        "initial_frozen":lab.INITIAL_WEIGHT,
        "pruned_zero":0.0,
        "inverted_reward":reversed_weight
    }
    scores={}
    for name,w in conditions.items():
        dataset=lab.collect(upstream,FRESH_FINAL,w)
        scores[name]={"weight":w,**lab.eval_model(model,dataset),
                      "example_AB":dataset[(0,"AB")]["spikes"],
                      "example_BA":dataset[(0,"BA")]["spikes"]}
    return {
        "experiment":"006b_bounded_multi_context_selection",
        "scope":"post-hoc modified algorithm following 006 failure; independent final split",
        "fixed_decoder_fit_contexts":lab.TRAIN,
        "reward_experience_contexts":EXPERIENCES,
        "fresh_final_contexts":FRESH_FINAL,
        "frozen_decoder":model,
        "training":{"learning_rate":RATE,"max_update":MAX_UPDATE,
                    "delta":lab.DELTA,"two_contexts_per_update":True,
                    "resource_cost":0.0,"update_episodes":len(log)-1},
        "trained_weight_trajectory":log,
        "inverted_reward_trajectory":reverse_log,
        "heldout":scores,
        "limits":"External label-based reward; parameter chosen after seeing 006 failure; four capped updates do not imply robust or biological learning. Identical physical gate and readout throughout controls."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",default="PerceptionLab")
    p.add_argument("--out",default="results/006b_bounded_selection.json")
    args=p.parse_args()
    d=main(args.upstream)
    destination=ROOT/args.out
    destination.parent.mkdir(exist_ok=True,parents=True)
    destination.write_text(json.dumps(d,indent=2)+"\n")
    print("BEGIN_006B_RECEIPT")
    print(json.dumps(d,indent=2))
    print("END_006B_RECEIPT")
