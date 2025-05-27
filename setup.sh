#!/bin/bash

# Resolve absolute path
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_PDDL_DIR="$PROJECT_ROOT/data/raw_pddl"
ANON_PDDL_DIR="$PROJECT_ROOT/data/anon_pddl"

# Grab raw PDDL domains from pyperplan
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
