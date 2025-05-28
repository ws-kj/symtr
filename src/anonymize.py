# Anonymize PDDL domains and problems
# No typing support yet!

import re 
import json
import argparse
import os
from pddl_parser.PDDL import PDDL_Parser
from pathlib import Path 

PROJ_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_DIR / "data" / "raw_pddl"
ANON_DIR = PROJ_DIR / "data" / "anon_pddl"

verbose = False

def log(args):
    if verbose:
        print(args)

def serialize_literals(literals, var_map):
    out = []
    for lit in sorted(literals):
        pred, *args = lit
        args = [var_map.get(arg, arg) for arg in args]
        out.append(f"({pred} {' '.join(args)})")
    return out

def serialize_literal(pred, args):
    return f"({pred} {' '.join(args)})"

def serialize_condition(positive, negative):
    all_conds = []
    for tup in sorted(positive):
        pred, *args = tup 
        all_conds.append(serialize_literal(pred, args))
    for tup in sorted(negative):
        pred, *args = tup 
        all_conds.append(f"(not {serialize_literal(pred, args)})")
    if not all_conds:
        return "()"
    if len(all_conds) == 1:
        return all_conds[0]
    return f"(and {' '.join(all_conds)})"

def serialize_effect(adds, deletes):
    return serialize_condition(adds, deletes)

def emit_anonymous_domain(anon_domain_path: Path, parser: PDDL_Parser, symbols: dict[str, str]):
    """
    Construct and save anonymized domain from parser
    """
    lines = []

    # header
    lines.append(f"(define (domain {parser.domain_name})")

    # requirements
    if parser.requirements:
        reqs = " ".join(f"{req}" for req in sorted(parser.requirements))
        lines.append(f"  (:requirements {reqs})")

    # types
    if parser.types:
        lines.append("  (:types")
        for base, subs in parser.types.items():
            lines.append(f"    {' '.join(subs)} - {base}")
        lines.append("  )")

    # predicates
    lines.append("  (:predicates")
    for pred, args in parser.predicates.items():
        typed_args = [f"{var} - {typ}" for var, typ in args.items()]
        lines.append(f"    ({pred} {' '.join(typed_args)})")
    lines.append("  )")

    # actions
    for action in parser.actions:
        lines.append(f"  (:action {action.name}")
        if action.parameters:
            typed_params = [f"{p} - {t}" for p, t in action.parameters]
            lines.append(f"    :parameters ({' '.join(typed_params)})")
        else:
            lines.append("    :parameters ()")

        # get scoped parameters
        param_map = {real: anon for anon, real in symbols.items() if anon.startswith(f"?{action.name}_")}

        # preconditions
        pre = serialize_literals(action.positive_preconditions, param_map)
        neg = serialize_literals(action.negative_preconditions, param_map)
        pre_strs = pre + [f"(not {n})" for n in neg]
        lines.append(f"    :precondition {'(and ' + ' '.join(pre_strs) + ')' if len(pre_strs) > 1 else pre_strs[0] if pre_strs else '()'}")

        # effects
        add = serialize_literals(action.add_effects, param_map)
        delete = serialize_literals(action.del_effects, param_map)
        eff_strs = add + [f"(not {d})" for d in delete]
        lines.append(f"    :effect {'(and ' + ' '.join(eff_strs) + ')' if len(eff_strs) > 1 else eff_strs[0] if eff_strs else '()'}")

        lines.append("  )")

    anon_domain_path.parent.mkdir(parents=True, exist_ok=True)
    with open(anon_domain_path, "w") as f:
        f.write("\n".join(lines))


def anonymize_domain(filename: str, domain_dir: Path):
    """
    Generate anonymized PDDL domain
    Creates new PDDL file + symbols.json with symbol mapping
    """
    domain_path = domain_dir / filename
    anon_domain_path = ANON_DIR / domain_dir.name / filename
    symbols_path = ANON_DIR / domain_dir.name / f"{Path(filename).stem}_symbols.json"

    # mapping of anonymous symbols -> real
    symbols = {}
    parser = PDDL_Parser()
    parser.parse_domain(domain_path)

    symbols["planning_domain"] = parser.domain_name
    parser.domain_name = "planning_domain"

    # parse types
    type_names = set(parser.types.keys())
    for children in parser.types.values():
        type_names.update(children)

    type_map = {"object": "object"} # keep base
    for i, name in enumerate(sorted(type_names)):
        if name != "object":
            # keep it backwards for looking when updating parser
            type_map[name] = f"type_{i}"

    symbols.update({v: k for k, v in sorted(type_map.items())})

    # update parser internal repr
    new_types = {}
    for parent, children in parser.types.items():
        new_parent = type_map.get(parent, parent)
        new_children = [type_map.get(child, child) for child in children]
        new_types[new_parent] = new_children
    parser.types = new_types

    # parse predicates + their parameters
    pred_map = {}
    new_predicates = {}
    for i, (pred, param_dict) in enumerate(parser.predicates.items()):
        pred_anon = f"pred_{i}"
        symbols[pred_anon] = pred
        pred_map[pred] = pred_anon

        new_params = {}
        for j, (param, typ) in enumerate(param_dict.items()):
            anon_param = f"?{pred_anon}_var{j}"
            symbols[anon_param] = param 
            new_params[anon_param] = type_map.get(typ, typ)

        new_predicates[pred_anon] = new_params
    parser.predicates = new_predicates

    # parse actions + their parameters
    action_map = {}
    new_actions = []
    for i, action in enumerate(parser.actions):
        act_anon = f"act_{i}"
        symbols[act_anon] = action.name
        action_map[action.name] = act_anon
        action.name = act_anon

        new_params = []
        for j, (param, typ) in enumerate(action.parameters):
            anon_param = f"?{act_anon}_var{j}"
            symbols[anon_param] = param
            new_params.append((anon_param, type_map.get(typ, typ)))
        action.parameters = new_params
        new_actions.append(action)
    parser.actions = new_actions
    breakpoint()
    # save new files
    anon_domain_path.parent.mkdir(parents=True, exist_ok=True)
    emit_anonymous_domain(anon_domain_path, parser, symbols)

    with open(symbols_path, "w") as f:
        json.dump(symbols, f, indent=2)

    log(symbols)
    log(f"\nAnonymized domain: {domain_path}")

def anonymize_task(filename: str, domain_dir: Path):
    """
    Generate anonymized PDDL problem
    """
    task_path = domain_dir / filename
    anon_task_path = ANON_DIR / domain_dir.name / filename
    symbols_task_path = ANON_DIR / domain_dir.name / f"{Path(filename).stem}_symbols.json"
    domain_symbols_path = ANON_DIR / domain_dir.name / f"domain_symbols.json"

    symbols = {}


    anonymized_text = ''
    # save new PDDL file
    anon_task_path.parent.mkdir(parents=True, exist_ok=True)
    with open(anon_task_path, "w") as f:
        f.write(anonymized_text)

    # flip for ease of decoding later
    flipped_symbols = {v: k for k, v in symbols.items()}
    with open(symbols_task_path, "w") as f:
        json.dump(flipped_symbols, f, indent=2)

    log(symbols)
    log(f"\nAnonymized task: {task_path}")
    

def anonymize_all():
    """
    Anonymize all .pddl in data/raw_pddl, and save to data/anon_pddl
    """
    try:
        for domain_dir in RAW_DIR.iterdir():
            anonymize_directory(str(domain_dir.resolve()))

    except FileNotFoundError as e:
        print(f"{e}")
        print("No raw PDDL directory? Run ../setup.sh to populate raw PDDL data.")

def anonymize_directory(dir: str):
    """
    Anonymize everything in specific domain directory
    """
    try:
        domain_dir = Path(RAW_DIR / dir)
        if not domain_dir.is_dir():
            print(f"{domain_dir} is not a directory.")
            return 

        for domain_file in domain_dir.glob("domain*.pddl"):
            anonymize_domain(domain_file.name, domain_dir)

            for task_file in domain_dir.glob("task*.pddl"):
                anonymize_task(task_file.name, domain_dir)
        
    except FileNotFoundError as e:
        print(f"{e}")
        print("No raw PDDL directory? Run ../setup.sh to populate raw PDDL data.")
        
def restore_file(anon_path: Path, symbol_path: Path):
    """
    Restore an anonymized PDDL file from a symbols.json file
    """

    with open(anon_path, "r") as f:
        anon_text = f.read()

    # symbols stored as anon -> original
    with open(symbol_path, "r") as f:
        symbols = json.load(f)

    # restore original symbols
    def replace_token(match):
        token = match.group(0)
        return symbols.get(token, token)
    token_pattern = r"[a-zA-Z_?][a-zA-Z0-9_\-]*"
    restored_text = re.sub(token_pattern, replace_token, anon_text)

    # save restored file
    restored_path = anon_path.parent / f"{anon_path.stem}_restored.pddl"
    with open(restored_path, "w") as f:
        f.write(restored_text)

    return restored_path

def restore_directory(dir_path: Path):
    """
    Restore all anon files in dir, assuming they have corresponding symbol table
    """

    for pddl_file in dir_path.glob("*.pddl"):
        symbol_file = dir_path / f"{pddl_file.stem}_symbols.json"
        if not symbol_file.exists():
            log(f"No symbol map found for {pddl_file.name}, skipping.")
            continue

        restored_path = restore_file(pddl_file, symbol_file)
        log(f"Restored: {restored_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--domain", type=str, help="Anonymize specific domain directory")
    parser.add_argument("--restore", type=str, help="Restore all PDDL files in directory")
#    parser.add_argument("--task", type=str, help="Anonymize specific task file")
    parser.add_argument("--all", action="store_true", help="Anonymize all raw PDDL")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    verbose = args.verbose

    if args.all:
        anonymize_all()
    elif args.domain:
        anonymize_directory(args.domain)
    elif args.restore:
        restore_directory(Path(args.restore))
    else:
        parser.print_help()
