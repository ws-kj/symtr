# Anonymize PDDL domains and problems

import pddlpy 
import argparse
import os 
from pathlib import Path 

PROJ_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_DIR / "data" / "raw_pddl"
ANON_DIR = PROJ_DIR / "data" / "anon_pddl"

def anonymize_domain_file(rel_path):
    """
    * Find relevant symbols:
        domain name
        predicate names
        type names
        action names
    * Replace all symbols in file
    * Save domain conversion metadata
    """
    pass

def anonymize_task_file(rel_path):
    """
    * Load domain conversion metadata
    * Replace domain symbols
    * Replace object names
    * Save task conversion metadata
    """
    pass

def anonymize_all():
    """
    For all folders in data/raw_pddl:
        convert domain.pddl
        convert task*.pddl
    Save in data/anon_pddl
    """
    for domain_dir in RAW_DIR.iterdir():
        if not domain_dir.is_dir():
            continue 

        domain_path = domain_dir / "domain.pddl"
        anon_domain_path = ANON_DIR / domain_dir.name / "domain.pddl"
        meta_domain_path = ANON_DIR / domain_dir.name / "domain_meta.json"

        anonymize_domain_file(domain_path)

        for task_file in domain_dir.glob("task*.pddl"):
            task_name = task_file.name 
            anon_task_path = ANON_DIR / domain_dir.name / task_name 
            meta_task_path = ANON_DIR / domain_dir.name / f"{task_name}_meta.json"

            anonymize_task_file(task_file.resolve())

    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--domain", type=str, help="Anonymize specific domain file")
    parser.add_argument("--task", type=str, help="Anonymize specific task file")
    parser.add_argument("--all", action="store_true", help="Anonymize all raw PDDL")

    args = parser.parse_args()
    if args.all:
        anonymize_all()
    elif args.domain:
        anonymize_domain_file(args.domain)
    elif args.task:
        anonymize_task_file(args.task)
    else:
        parser.print_help()
