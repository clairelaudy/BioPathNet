import re
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def load(filename):
    data = set()
    with open(filename) as fd:
        for line in fd:
            triple = tuple(line.strip().split("\t"))
            data.add(triple)
    return data


def is_in(source,edge,target, skg):
    if (source,edge,target) in skg  \
    or (target,edge.replace("rev_", ""),source) in skg:
        return True
    else:
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("ranked_edges")
    parser.add_argument("skg_learned")
    parser.add_argument("skg_expected")
    parser.add_argument("edges_known")

    asked = parser.parse_args()

    skg_learned = load(asked.skg_learned)
    skg_expected = load(asked.skg_expected)
    edges_known = load(asked.edges_known)

    ranks = pd.read_csv(asked.ranked_edges, sep="\t", usecols=["query_node", "query_relation", "pred_node", "prediction_score"])
    ranks["reverse"] = False
    ranks["in_learned"] = False
    ranks["in_expected"] = False
    ranks["known"] = False
    ranks["name"] = ranks["query_node"]+ranks["query_relation"]+ranks["pred_node"]
    ranks["predicted_edge"] = ""
    ranks["type"] = ""
    score_min = ranks["prediction_score"].min()
    score_max = ranks["prediction_score"].max()
    ranks["score"] = (ranks["prediction_score"] - score_min) / (score_max - score_min)

    for i,row in ranks.iterrows():
        source,edge,target = (ranks.loc[i, "query_node"], ranks.loc[i, "query_relation"], ranks.loc[i, "pred_node"])

        reverse_tag = "forward"
        if re.match("^rev_", edge):
            ranks.loc[i, "reverse"] = True
            reverse_tag = "reverse"

        in_learned_tag = "forgot"
        if is_in(source,edge,target, skg_learned):
            ranks.loc[i, "in_learned"] = True
            in_learned_tag = "learned"

        in_expected_tag = "unexpected"
        if is_in(source,edge,target, skg_expected):
            ranks.loc[i, "in_expected"] = True
            in_expected_tag = "expected"

        known_tag = "unknown"
        if is_in(source,edge,target, edges_known):
            ranks.loc[i, "known"] = True
            known_tag = "known"

        ranks.loc[i, "type"] = "_".join([known_tag, in_learned_tag, in_expected_tag, reverse_tag])
        ranks.loc[i, "predicted_edge"] = ranks.loc[i, "name"] + "_" + ranks.loc[i, "type"]

    f, ax = plt.subplots(figsize=(6, 15))
    bp = sns.barplot(data = ranks, x = "score", y = "predicted_edge", hue = "type", edgecolor = None, width = 1)
    ax.set(yticklabels=[])
    ax.set_yticks([])
    fig = bp.get_figure()

    fig.savefig("ranks.pdf")

    print("ranks.pdf")

