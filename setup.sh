#!/bin/bash

# Grab raw PDDL domains from pyperplan
mkdir -p data/raw_pddl
mkdir -p data/anon_pddl
cd data/raw_pddl
git clone --filter=blob:none --no-checkout https://github.com/aibasel/pyperplan.git temp_repo
cd temp_repo
git sparse-checkout init --cone
git sparse-checkout set benchmarks
git checkout
mv benchmarks/* ../
cd ..
rm -rf temp_repo
