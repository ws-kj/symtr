#!/bin/bash

# resolve absolute path
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_PDDL_DIR="$PROJECT_ROOT/data/raw_pddl"
ANON_PDDL_DIR="$PROJECT_ROOT/data/anon_pddl"

rm -rf "$RAW_PDDL_DIR"

# grab raw PDDL domains from pyperplan
mkdir -p "$RAW_PDDL_DIR"
mkdir -p "$ANON_PDDL_DIR"
cd "$RAW_PDDL_DIR"
git clone --filter=blob:none --no-checkout https://github.com/aibasel/pyperplan.git temp_repo
cd temp_repo
git sparse-checkout init --cone
git sparse-checkout set benchmarks
git checkout
mv benchmarks/* "$RAW_PDDL_DIR/" 
cd "$RAW_PDDL_DIR"
rm -rf temp_repo

# get rid of unparsable domains

KEEP_DIRS=("elevators" "logistics" "openstacks" "psr-small" "scanalyzer" "transport" "blocks" "freecell" "miconic" "parcprinter" "rovers" "sokoban" "woodworking" "depot" "gripper" "movie" "pegsol" "satellite" "tpp")


for dir in "$RAW_PDDL_DIR"/*; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        keep=false
        for keep_dir in "${KEEP_DIRS[@]}"; do
            if [ "$dirname" = "$keep_dir" ]; then
                keep=true
                break
            fi
        done
        if [ "$keep" = false ]; then
            rm -rf "$dir"
        fi
    fi
done

# anonymize pddl
for domain in "${KEEP_DIRS[@]}"; do 
    python3 "$PROJECT_ROOT/src/anonymize.py" --verbose --domain "$domain"
done
