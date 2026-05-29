import os
import logging
import argparse
import subprocess, sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description="Arguments to access the main functions of BioPathNets")
parser.add_argument("-f", "--function",    type=str, nargs=1,   default="run", help="the script to be called (run, predict, visualize, ...)", required=True)
parser.add_argument("-c", "--config",      type=str, nargs=1,   default="config/mock/mock_data_run.yaml", help="path to the YAML configuration file.", required=True)
parser.add_argument("-g", "--gpus",        type=str, nargs=1,   default="null", help="the list of gpus to be used. Eg [0]", required=True)
parser.add_argument("-s", "--seed",        type=int, nargs="?", default=None)
parser.add_argument("-cp", "--checkpoint", type=str, nargs="?", default=None, help="path to the stored trained model to be used.")
parser.add_argument("-b", "--biopathnet", type=str, default=".", help="Path to BioPathNet source directory")
args = parser.parse_args()

logger.debug(f"Args = {args}")

cmd = []
function = args.function[0]

# Update the config files in order to have the right paths
# wild_card = "{{BIOPATHNET}}"
# cwd = os.getcwd()
config_in = args.config[0]
# config_out = "".join([config_in[:-5], "_apptainer.yaml"])
# with open(config_in, 'r') as cfi:
#     lines = cfi.read()
#     lines = lines.replace(wild_card, cwd)

# with open(config_out, 'w') as cfo:
#     cfo.write(lines)

if function=="run":
    cmd = ["python", f"{args.biopathnet}/script/{function}.py",
                "-c", config_in,
                "--gpus", args.gpus[0]
            ]

elif (function=="predict" or
    function=="eval_and_predict" or
    function=="eval_and_predict_inductive" or
    function=="visualize" or
    function=="visualize_graph" or
    function=="visualize_inductive"):
    if not args.checkpoint:
        logger.error(f"ERROR: Missing --checkpoint option for the {function} function")
    cmd = ["python", f"{args.biopathnet}/script/{function}.py",
                "-c", config_in,
                "--gpus", args.gpus[0],
                "--checkpoint", args.checkpoint
    ]

else:
    logger.error(f"Function {function} is not supported by the api.")
    logger.error(f"Supported functions: run, predict, eval_and_predict, eval_and_predict_inductive, visualize, visualize_inductive")

if args.seed:
    cmd.append([cmd, "-s", args.seed[0]])

logger.info(f"BioPathNet call command = {cmd}")

subprocess.run(cmd)
