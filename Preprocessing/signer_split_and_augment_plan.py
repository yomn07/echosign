"""
Signer-Aware Train/Val/Test Split + Train-Side Augmentation Planner
===================================================================

Changes:
- Global signer ranking
- Train signers selected by SAMPLE COVERAGE
- Held-out signers split into validation/test
- Per-class signer validation
- Augmentation only for valid classes

"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import math


# ------------------------------------------------------------
# Loading
# ------------------------------------------------------------

def load_entries(path):

    entries = []

    with open(path, encoding="utf-8") as f:

        for line in f:

            line=line.strip()

            if line:
                entries.append(json.loads(line))

    return entries



def canonical_id(e):

    return e.get(
        "canonical_signer_id",
        f"{e['source']}:{e['signer_id']}"
    )


# ------------------------------------------------------------
# Global signer ranking
# ------------------------------------------------------------

def rank_signers(entries):

    totals = defaultdict(int)

    for e in entries:

        totals[canonical_id(e)] += 1


    return sorted(
        totals.items(),
        key=lambda x:x[1],
        reverse=True
    )



# ------------------------------------------------------------
# Sample weighted train split
# ------------------------------------------------------------

def assign_pools_by_samples(
        ranked,
        train_sample_fraction=0.85
):

    total_samples = sum(
        count for _,count in ranked
    )


    target = total_samples * train_sample_fraction


    train_pool=set()

    current=0

    heldout=[]


    for signer,count in ranked:


        if current + count <= target:

            train_pool.add(signer)

            current += count

        else:

            heldout.append(
                (signer,count)
            )


    val_pool=set()
    test_pool=set()


    # alternate remaining signers
    # to avoid putting only weak signers in one pool

    for i,(signer,_) in enumerate(heldout):

        if i%2==0:

            val_pool.add(signer)

        else:

            test_pool.add(signer)


    return (
        train_pool,
        val_pool,
        test_pool
    )



# ------------------------------------------------------------
# Assign sample splits
# ------------------------------------------------------------

def assign_split(
        entries,
        train_pool,
        val_pool,
        test_pool
):

    for e in entries:

        sid=canonical_id(e)


        if sid in train_pool:

            e["split_assignment"]="train"


        elif sid in val_pool:

            e["split_assignment"]="val"


        elif sid in test_pool:

            e["split_assignment"]="test"


        else:

            e["split_assignment"]="unknown"


    return entries



# ------------------------------------------------------------
# Class validation
# ------------------------------------------------------------

def class_report(
        entries,
        min_train_signers=3,
        min_heldout_signers=2
):


    classes=defaultdict(list)


    for e in entries:

        classes[e["label"]].append(e)



    report=[]


    for label,rows in classes.items():


        train=[
            r for r in rows
            if r["split_assignment"]=="train"
        ]

        val=[
            r for r in rows
            if r["split_assignment"]=="val"
        ]

        test=[
            r for r in rows
            if r["split_assignment"]=="test"
        ]


        train_signers={
            canonical_id(r)
            for r in train
        }


        heldout_signers={
            canonical_id(r)
            for r in val+test
        }



        passed=(

            len(train_signers)>=min_train_signers

            and

            len(heldout_signers)>=min_heldout_signers

        )


        report.append({

            "label":label,

            "text":rows[0]["text"],


            "train_samples":len(train),

            "val_samples":len(val),

            "test_samples":len(test),


            "train_signers":
                len(train_signers),


            "heldout_signers":
                len(heldout_signers),


            "passes_floor":
                passed

        })


    report.sort(
        key=lambda x:
        (
            x["passes_floor"],
            x["train_samples"]
        )
    )


    return report
# ------------------------------------------------------------
# Train-side augmentation planner
# ------------------------------------------------------------

def compute_augmentation_plan(
        entries,
        class_report,
        mid_low=15,
        mid_high=29,
        target=30,
        max_multiplier=5
):

    # keep only classes that passed signer requirements

    valid_classes = {
        c["label"]
        for c in class_report
        if c["passes_floor"]
    }


    train_rows = [
        e for e in entries
        if e["split_assignment"]=="train"
    ]


    by_class=defaultdict(list)


    for r in train_rows:

        if r["label"] in valid_classes:

            by_class[r["label"]].append(r)



    plan={}


    for label,rows in by_class.items():


        total_real=len(rows)


        if total_real < mid_low or total_real > mid_high:

            continue



        text=rows[0]["text"]


        signer_counts=Counter(
            canonical_id(r)
            for r in rows
        )


        n_signers=len(signer_counts)


        if n_signers==0:

            continue



        # desired samples per signer

        per_signer_target=math.ceil(
            target/n_signers
        )



        deficits={}


        for signer,count in signer_counts.items():

            deficits[signer]=max(
                0,
                per_signer_target-count
            )


        budget=target-total_real


        allocation={}


        if budget<=0:

            allocation={
                s:0
                for s in signer_counts
            }


        else:


            total_deficit=sum(
                deficits.values()
            )


            if total_deficit <= budget:


                allocation=dict(deficits)


                leftover=(
                    budget-total_deficit
                )


                if leftover>0:


                    for s,c in signer_counts.items():

                        allocation[s]+=round(
                            leftover*c/total_real
                        )


            else:


                for s,d in deficits.items():

                    allocation[s]=round(
                        d*budget/total_deficit
                    )


                diff=(
                    budget-
                    sum(allocation.values())
                )


                if diff!=0:


                    biggest=max(
                        allocation,
                        key=allocation.get
                    )


                    allocation[biggest]+=diff



        # apply augmentation cap

        capped={}


        for signer,aug in allocation.items():

            real=signer_counts[signer]


            cap=max_multiplier*real


            capped[signer]=min(
                aug,
                cap
            )



        plan[str(label)]={

            "text":text,

            "real_samples":total_real,

            "signers":n_signers,

            "samples_per_signer":
                dict(signer_counts),

            "augment_per_signer":
                capped,

            "total_augmented":
                sum(capped.values()),

            "final_samples":
                total_real+
                sum(capped.values())

        }


    return plan



# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    parser=argparse.ArgumentParser()


    parser.add_argument(
        "--input",
        required=True
    )


    parser.add_argument(
        "--out_dir",
        default="merged_output/split"
    )


    parser.add_argument(
        "--train_frac",
        type=float,
        default=0.85
    )


    parser.add_argument(
        "--min_train_signers",
        type=int,
        default=3
    )


    parser.add_argument(
        "--min_heldout_signers",
        type=int,
        default=2
    )


    parser.add_argument(
        "--mid_low",
        type=int,
        default=15
    )


    parser.add_argument(
        "--mid_high",
        type=int,
        default=29
    )


    parser.add_argument(
        "--target",
        type=int,
        default=30
    )


    parser.add_argument(
        "--max_multiplier",
        type=int,
        default=5
    )


    args=parser.parse_args()



    out=Path(args.out_dir)

    out.mkdir(
        parents=True,
        exist_ok=True
    )


    print("Loading entries...")

    entries=load_entries(
        args.input
    )

    print(
        " ",
        len(entries),
        "entries loaded"
    )



    print("\nRanking signers globally...")


    ranked=rank_signers(
        entries
    )


    print(
        " ",
        len(ranked),
        "signers"
    )


    print(
        " Top 5:",
        ranked[:5]
    )



    train_pool,val_pool,test_pool = assign_pools_by_samples(
        ranked,
        args.train_frac
    )



    print(
        "\nPool sizes:"
    )

    print(
        " train:",
        len(train_pool)
    )

    print(
        " val:",
        len(val_pool)
    )

    print(
        " test:",
        len(test_pool)
    )



    entries=assign_split(
        entries,
        train_pool,
        val_pool,
        test_pool
    )


    split_counts=Counter(
        e["split_assignment"]
        for e in entries
    )


    print(
        "\nSample split:"
    )

    print(
        split_counts
    )



    split_file=out/"split_assignment.jsonl"


    with open(split_file,"w",encoding="utf-8") as f:

        for e in entries:

            f.write(
                json.dumps(e)+"\n"
            )


    print(
        "Written:",
        split_file
    )



    print(
        "\nChecking classes..."
    )


    report=class_report(
        entries,
        args.min_train_signers,
        args.min_heldout_signers
    )


    passed=sum(
        1 for r in report
        if r["passes_floor"]
    )


    print(
        "Passing classes:",
        passed,
        "/",
        len(report)
    )



    report_file=out/"class_split_report.json"


    with open(report_file,"w") as f:

        json.dump(
            report,
            f,
            indent=2
        )



    print(
        "Written:",
        report_file
    )



    print(
        "\nCreating augmentation plan..."
    )


    plan=compute_augmentation_plan(
        entries,
        report,
        args.mid_low,
        args.mid_high,
        args.target,
        args.max_multiplier
    )



    aug_file=out/"augmentation_plan.json"


    with open(aug_file,"w") as f:

        json.dump(
            plan,
            f,
            indent=2
        )



    total_aug=sum(
        p["total_augmented"]
        for p in plan.values()
    )


    print(
        "Classes augmented:",
        len(plan)
    )

    print(
        "Synthetic samples:",
        total_aug
    )


    print(
        "Written:",
        aug_file
    )



if __name__=="__main__":

    main()