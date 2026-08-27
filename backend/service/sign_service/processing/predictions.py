def format_predictions(
    prediction,
    top_k=5,
):

    results = []

    for item in prediction[:top_k]:

        if isinstance(
            item,
            dict,
        ):

            results.append({
                "word": item["word"],
                "confidence":
                    float(
                        item["confidence"]
                    ),
            })

        else:

            results.append({
                "word": item[0],
                "confidence":
                    float(item[1]),
            })

    return results


def xy_pairs(
    landmarks,
    start,
    end,
):

    return [

        [
            float(landmarks[i]),
            float(
                landmarks[i + 1]
            ),
        ]

        for i in range(
            start,
            end,
            3,
        )
    ]