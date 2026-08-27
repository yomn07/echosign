import json
import argparse
from pathlib import Path
from collections import Counter


def load_jsonl(path):
    data = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                data.append(json.loads(line))

    return data



def save_jsonl(path, data):

    with open(path,"w",encoding="utf-8") as f:

        for item in data:
            f.write(
                json.dumps(item, ensure_ascii=False)
                + "\n"
            )



def main():

    parser=argparse.ArgumentParser()

    parser.add_argument(
        "--split_file",
        required=True,
        help="split_assignment.jsonl"
    )

    parser.add_argument(
        "--report_file",
        required=True,
        help="class_split_report.json"
    )

    parser.add_argument(
        "--out_dir",
        default="baseline_dataset"
    )


    args=parser.parse_args()


    out=Path(args.out_dir)
    out.mkdir(
        parents=True,
        exist_ok=True
    )


    print("Loading split file...")

    samples=load_jsonl(
        args.split_file
    )

    print(
        "Samples loaded:",
        len(samples)
    )



    print("\nLoading class report...")

    with open(
        args.report_file,
        encoding="utf-8"
    ) as f:

        report=json.load(f)



    # classes with enough signer diversity

    valid_labels=set(
        c["label"]
        for c in report
        if c["passes_floor"]
    )


    print(
        "Valid classes:",
        len(valid_labels)
    )



    # filter

    filtered=[
        x for x in samples
        if x["label"] in valid_labels
    ]



    print(
        "Samples after class filtering:",
        len(filtered)
    )



    # split

    train=[
        x for x in filtered
        if x["split_assignment"]=="train"
    ]


    val=[
        x for x in filtered
        if x["split_assignment"]=="val"
    ]


    test=[
        x for x in filtered
        if x["split_assignment"]=="test"
    ]



    print("\nFinal dataset")

    print("-----------------------------")

    print(
        "Train:",
        len(train)
    )

    print(
        "Val:",
        len(val)
    )

    print(
        "Test:",
        len(test)
    )



    print("\nClasses")

    print("-----------------------------")

    print(
        "Train classes:",
        len(set(x["label"] for x in train))
    )

    print(
        "Val classes:",
        len(set(x["label"] for x in val))
    )

    print(
        "Test classes:",
        len(set(x["label"] for x in test))
    )



    print("\nSigners")

    print("-----------------------------")

    print(
        "Train signers:",
        len(set(
            x["canonical_signer_id"]
            if "canonical_signer_id" in x
            else f'{x["source"]}:{x["signer_id"]}'
            for x in train
        ))
    )


    print(
        "Val signers:",
        len(set(
            x["canonical_signer_id"]
            if "canonical_signer_id" in x
            else f'{x["source"]}:{x["signer_id"]}'
            for x in val
        ))
    )


    print(
        "Test signers:",
        len(set(
            x["canonical_signer_id"]
            if "canonical_signer_id" in x
            else f'{x["source"]}:{x["signer_id"]}'
            for x in test
        ))
    )



    # class distribution

    print("\nTop 10 classes by train samples")

    counts=Counter(
        x["label"]
        for x in train
    )


    for label,count in counts.most_common(10):

        text=next(
            x["text"]
            for x in train
            if x["label"]==label
        )

        print(
            label,
            text,
            count
        )



    # save

    save_jsonl(
        out/"train_baseline.jsonl",
        train
    )

    save_jsonl(
        out/"val_baseline.jsonl",
        val
    )

    save_jsonl(
        out/"test_baseline.jsonl",
        test
    )



    print("\nWritten:")

    print(
        out/"train_baseline.jsonl"
    )

    print(
        out/"val_baseline.jsonl"
    )

    print(
        out/"test_baseline.jsonl"
    )



if __name__=="__main__":

    main()