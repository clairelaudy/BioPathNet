import re
import math
import random
import pathlib
import logging
import itertools

def src(s):
    res = set()
    for e in s:
        res.add(e[0])
    return res

def tgt(s):
    res = set()
    for e in s:
        res.add(e[-1])
    return res


def load(filename, max = 15):
    res = set()
    dups = set()
    logging.info(f"Load {filename} ...")
    with open(filename) as fd:
        lines = fd.readlines()
        logging.info(f"\t{len(lines)} lines")
        if len(lines) == 0:
            logging.error(f"\t{filename} contains no data")
        for line in lines:
            t = line.strip().split('\t')
            if tuple(t) in res:
                dups.add(tuple(t))
            else:
                res.add( tuple(t) )
        logging.info(f"\t{len(res)} triples")
        logging.info(f"\t{len( src(res) | tgt(res) )} unique objects (either source or target)")

    ndup = len(lines) - len(res)
    if ndup > 0:
        logging.debug(f"\tcontains {ndup} duplicates:")
        log_head(dups, max, indent = 2)
    else:
        logging.debug(f"\tcontains no duplicate")

    return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("input_skg")
    parser.add_argument("percent_validated", type = int)
    parser.add_argument("percent_tested", type = int)
    parser.add_argument("edge_type", default = ".*")

    parser.add_argument("--log-level", default = "DEBUG")

    asked = parser.parse_args()

    logging.basicConfig(format = "{levelname:^8s} {message}", style = '{')
    logger = logging.getLogger()
    level = logging.getLevelName(asked.log_level)
    logger.setLevel(level)

    skg = load(asked.input_skg)

    p = pathlib.Path(asked.input_skg)
    skg_name = p.stem
    skg_ext = p.suffix

    p_vali = asked.percent_validated
    p_test = asked.percent_tested

    edge_type = asked.edge_type

    skg_typed = []
    for triple in skg:
        if re.match(edge_type, triple[1]):
            skg_typed.append(triple)

    n = len(skg_typed)
    assert n > 0

    n_vali = int( math.ceil(p_vali * n / 100) )
    n_test = int( math.ceil(p_test * n / 100) )

    random.shuffle(skg_typed)

    data = {}
    data["validation"]  = skg_typed[0:n_vali]
    data["test"]  = skg_typed[n_vali:n_vali+n_test]

    assert len(data["validation"]) > 0
    if len(data["test"]) == 0:
        logging.warning("Test data is empty")

    s_vali = set(data["validation"])
    s_test = set(data["test"])

    data["train"] = skg.difference( s_vali.union(s_test) )

    for k in data:
        f = f"{skg_name}__{k}{skg_ext}"
        logging.info(f)
        with open(f, 'w') as fd:
            for triple in data[k]:
                n='\n'
                t='\t'
                fd.write(f"{t.join(triple)}{n}")
            logging.info(f"\t{len(data[k])} items")

