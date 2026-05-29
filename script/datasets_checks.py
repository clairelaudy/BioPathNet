import itertools
import logging

def log_head(s, max = 15, indent = 1):
    for i,e in enumerate(s):
        t = "\t" * indent
        logging.debug(f"{t}{i}. {e}")
        if i >= max:
            logging.debug(f"{t}[…]")
            break

def load(filename):
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
        log_head(dups, indent = 2)
    return res


def sources(data, k):
    return src(data[k])

def src(s):
    res = set()
    for e in s:
        res.add(e[0])
    return res


def targets(data, k):
    return tgt(data[k])

def tgt(s):
    res = set()
    for e in s:
        res.add(e[-1])
    return res


def check_no_intersection(data, lhs, rhs):
    inter = data[lhs].intersection(data[rhs])
    if inter:
        logging.error(f"{lhs} and {rhs} intersect on: {inter}")


def check_no_intersections(data, sets):
    for L,R in itertools.combinations(sets, 2):
        check_no_intersection(data, L, R)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--train", default="skg__train.txt")
    parser.add_argument("-v", "--valid", default="skg__validation.txt")
    parser.add_argument("-t", "--test", default="skg__test.txt")
    parser.add_argument("-n", "--names", default="entity_names.txt")
    parser.add_argument("-y", "--types", default="entity_types.txt")
    parser.add_argument("-b", "--brg", default="brg.txt")

    parser.add_argument("--log-level", default = "DEBUG")

    asked = parser.parse_args()

    logging.basicConfig(format = "{levelname:^8s} {message}", style = '{')
    logger = logging.getLogger()
    level = logging.getLevelName(asked.log_level)
    logger.setLevel(level)

    data = {}
    data["test"]  = load(asked.test)
    data["train"] = load(asked.train)
    data["valid"] = load(asked.valid)
    data["names"] = load(asked.names)
    data["types"] = load(asked.types)
    data["brg"]   = load(asked.brg)

    if sources(data, "names") != sources(data, "types"):
        logging.error(f"{asked.types} and {asked.names} do not have the same elements IDs")

    check_no_intersections(data, ["train", "valid", "test"])

    all_names = \
          sources(data, "train") | targets(data, "train") \
        | sources(data, "valid") | targets(data, "valid") \
        | sources(data, "test")  | targets(data, "test")  \
        | sources(data, "brg")  | targets(data, "brg")

    recorded = sources(data, "names")
    if recorded != all_names:
        n_recorded = len(recorded)
        n_all = len(all_names)
        symdiff = recorded.symmetric_difference(all_names)
        logging.error(f"{n_recorded} input names (train+valid+test+brg) differ from {n_all} {asked.names} by {len(symdiff)}")
        if symdiff:
            log_head(symdiff)
