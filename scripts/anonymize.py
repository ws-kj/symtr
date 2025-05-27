# Anonymize PDDL domains and problems
import re 
import json
import pddlpy 
import argparse
import os 
from pathlib import Path 

PROJ_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_DIR / "data" / "raw_pddl"
ANON_DIR = PROJ_DIR / "data" / "anon_pddl"

verbose = False

def log(args):
    if verbose:
        print(args)

def anonymize_domain(filename: str, domain_dir: Path):
    """
    Generate anonymized PDDL domain and save symbol mapping
    """
    domain_path = domain_dir / filename
    anon_domain_path = ANON_DIR / domain_dir.name / filename
    symbols_path = ANON_DIR / domain_dir.name / f"{Path(filename).stem}_symbols.json"

    # mapping of named symbols -> anonymous
    symbols = {}

    # need to manually extract domain name with regex
    with open(domain_path, "r") as f:
        domain_text = f.read()
    domain_name_match = re.search(r"\(define\s*\(domain\s+([^)]+)\)", domain_text)
    domain_name = domain_name_match.group(1) if domain_name_match else "unknown_domain"
    symbols[domain_name] = "domain"

    # pass domain_path as dummy task
    try:
        domain = pddlpy.DomainProblem(domain_path, domain_path).domain
    except FileNotFoundError as _:
        log("Couldn't open domain file!")
        return

    # parse and anonymize PDDL symbols
    for i, obj in enumerate(domain.objects.keys()):
        symbols[obj] = f"predicate_{i}"
    for i, op in enumerate(domain.operators.keys()):
        symbols[op] = f"action_{i}"
    for op in domain.operators.values():
        for i, var in enumerate(op.variable_list.keys()):
            symbols[var] = f"?variable_{i}"

    # replace symbols
    def replace_token(match):
        token = match.group(0)
        return symbols.get(token, token)
    token_pattern = r"[a-zA-Z_?][a-zA-Z0-9_\-]*"
    anonymized_text = re.sub(token_pattern, replace_token, domain_text)

    # save new PDDL file
    anon_domain_path.parent.mkdir(parents=True, exist_ok=True)
    with open(anon_domain_path, "w") as f:
        f.write(anonymized_text)

    # create symbol mapping. flip for ease of decoding later
    flipped_symbols = {v: k for k, v in symbols.items()}
    with open(symbols_path, "w") as f:
        json.dump(flipped_symbols, f, indent=2)

    log(symbols)
    log(f"\nAnonymized domain: {domain_path}")

def anonymize_task(filename: str, domain_dir: Path):
    """
    * Load domain conversion symbols
    * Replace domain symbols
    * Replace object names
    * Save task conversion symbols
    """
    anon_task_path: str = ANON_DIR / domain_dir.name / filename 
    symbols_task_path: str = ANON_DIR / domain_dir.name / f"{filename}_symbols.json"

    

def anonymize_all(verbose: bool = False):
    """
    For all folders in data/raw_pddl:
        convert domain.pddl
        convert task*.pddl
    Save in data/anon_pddl
    """
    #try:
    for domain_dir in RAW_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        for domain_file in domain_dir.glob("domain*.pddl"):
            anonymize_domain(domain_file.name, domain_dir)
        break

            #for task_file in domain_dir.glob("task*.pddl"):

            #    anonymize_task(task_file.name, domain_dir)
    #except FileNotFoundError as _:
    #    print("No raw PDDL directory! Run ../setup.sh to populate raw PDDL data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

#    parser.add_argument("--domain", type=str, help="Anonymize specific domain file")
#    parser.add_argument("--task", type=str, help="Anonymize specific task file")
    parser.add_argument("--all", action="store_true", help="Anonymize all raw PDDL")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    verbose = args.verbose

    if args.all:
        anonymize_all()
    else:
        parser.print_help()
