import itertools
import logging

def log_head(s, max = 15, indent = 1):
    for i,e in enumerate(s):
        t = "\t" * indent
        logging.debug(f"{t}{i}. {e}")
        if i >= max:
            logging.debug(f"{t}[…]")
            break

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


def names(s):
    return src(s) | tgt(s)


def check_no_intersection(data, lhs, rhs):
    inter = data[lhs].intersection(data[rhs])
    if inter:
        logging.error(f"{lhs} ({len(data[lhs])} items) and {rhs} ({len(data[rhs])} items) intersect on {len(inter)} items:")
        log_head(inter)
    else:
        logging.info(f"{lhs} and {rhs} do not intersect")


def check_no_intersections(data, sets):
    for L,R in itertools.combinations(sets, 2):
        check_no_intersection(data, L, R)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--train", default="skg__train.txt")
    parser.add_argument("-v", "--valid", default="skg__validation.txt")
    parser.add_argument("-t", "--test", default="skg__test.txt")
    parser.add_argument("-b", "--brg", default="brg.txt")
    parser.add_argument("-s", "--skg", default="skg.txt")
    parser.add_argument("-y", "--types", default="entity_types.txt")
    parser.add_argument("-n", "--names", default="entity_names.txt")

    parser.add_argument("--log-level", default = "DEBUG")
    parser.add_argument("--max", default = 5)


    asked = parser.parse_args()

    logging.basicConfig(format = "{levelname:^8s} {message}", style = '{')
    logger = logging.getLogger()
    level = logging.getLevelName(asked.log_level)
    logger.setLevel(level)

    data = {}
    data["test"]  = load(asked.test, asked.max)
    data["train"] = load(asked.train, asked.max)
    data["valid"] = load(asked.valid, asked.max)
    data["brg"]   = load(asked.brg, asked.max)
    data["skg"]   = load(asked.skg, asked.max)
    data["types"] = load(asked.types, asked.max)
    data["names"] = load(asked.names, asked.max)

    if sources(data, "names") == sources(data, "types"):
        logging.info(f"{asked.types} and {asked.names} have the same elements IDs")
    else:
        logging.error(f"{asked.types} and {asked.names} DO NOT have the same elements IDs")

    if data["skg"] == data["train"] | data["valid"] | data["test"]:
        logging.info(f"{asked.skg} is the same than the union of train+valid+test")
    else:
        logging.error(f"{asked.skg} is NOT the same than the union of train+valid+test")

    check_no_intersections(data, ["train", "valid", "test"])

    all_names = \
          sources(data, "train") | targets(data, "train") \
        | sources(data, "valid") | targets(data, "valid") \
        | sources(data, "test")  | targets(data, "test")  \
        | sources(data, "brg")  | targets(data, "brg")

    recorded = sources(data, "names")
    if recorded == all_names:
        logging.info(f"{asked.names} and input SKG names (train+valid+test+brg) are the same")
    else:
        n_recorded = len(recorded)
        n_all = len(all_names)
        symdiff = recorded.symmetric_difference(all_names)
        if symdiff:
            logging.error(f"{n_recorded} input SKG names (train+valid+test+brg) differ from {n_all} sources in {asked.names}:")
            logging.error(f"There's {len(symdiff)} names that differs.")

            recorded_diff = recorded.difference(all_names)
            if recorded_diff:
                logging.error(f"There's {len(recorded_diff)} names that are in {asked.names} but not in input SKG names (train+valid+test+brg)")
                log_head(recorded_diff, asked.max)

            all_diff = all_names.difference(recorded)
            if all_diff:
                logging.error(f"There's {len(all_diff)} names that are in input SKG names (train+valid+test+brg) but not in {asked.names}")
                log_head(all_diff, asked.max)

                for k in ["train", "valid", "test", "brg"]:
                    diff = names(data[k]).difference(recorded)
                    if diff:
                        logging.error(f"There's {len(diff)} names that are in {vars(asked)[k]} but not in {asked.names}")
                        log_head(diff, asked.max)
                    else:
                        logging.info(f"All names in {vars(asked)[k]} are in {asked.names}")

