import re
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("ranked_edges")
    parser.add_argument("skg_learned")
    parser.add_argument("skg_expected")

    asked = parser.parse_args()

    skg_learned = set()
    with open(asked.skg_learned) as fd:
        for line in fd:
            triple = tuple(line.strip().split("\t"))
            skg_learned.add(triple)

    skg_expected = set()
    with open(asked.skg_expected) as fd:
        for line in fd:
            triple = tuple(line.strip().split("\t"))
            skg_expected.add(triple)

    ranks = pd.read_csv(asked.ranked_edges, sep="\t", usecols=["query_node", "query_relation", "pred_node", "prediction_score"])
    ranks["reverse"] = False
    ranks["in_learned"] = False
    ranks["in_expected"] = False
    ranks["name"] = ranks["query_node"]+ranks["query_relation"]+ranks["pred_node"]
    ranks["predicted_edge"] = ""
    ranks["type"] = ""
    score_min = ranks["prediction_score"].min()
    score_max = ranks["prediction_score"].max()
    ranks["score"] = (ranks["prediction_score"] - score_min) / (score_max - score_min)

    for i,row in ranks.iterrows():
        source,edge,target = (ranks.loc[i, "query_node"], ranks.loc[i, "query_relation"], ranks.loc[i, "pred_node"])

        reverse_tag = "r"
        if re.match("^rev_", edge):
            ranks.loc[i, "reverse"] = True
            reverse_tag = "R"

        in_learned_tag = "l"
        if (source,edge,target) in skg_learned  \
        or (target,edge.replace("rev_", ""),source) in skg_learned:
            ranks.loc[i, "in_learned"] = True
            in_learned_tag = "L"

        in_expected_tag = "e"
        if (source,edge,target) in skg_expected  \
        or (target,edge.replace("rev_", ""),source) in skg_expected:
            ranks.loc[i, "in_expected"] = True
            in_expected_tag = "E"

        ranks.loc[i, "type"] = in_learned_tag + in_expected_tag + reverse_tag
        ranks.loc[i, "predicted_edge"] = ranks.loc[i, "name"] + "_" + ranks.loc[i, "type"]

    f, ax = plt.subplots(figsize=(6, 15))
    bp = sns.barplot(data = ranks, x = "score", y = "predicted_edge", hue = "type", edgecolor = None, width = 1)
    ax.set(yticklabels=[])
    ax.set_yticks([])
    fig = bp.get_figure()

    fig.savefig("ranks.pdf")

    print("ranks.pdf")

