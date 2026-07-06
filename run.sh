#!/usr/bin/env bash
#SBATCH -o compile.out
#SBATCH -e compile.err
#SBATCH -t 47:55:00
#SBATCH -p risc5

echo $DATE
source util/setchplenv.bash
CHPL_TARGET_CPU=riscv64 CHPL_TEST_TIMEOUT=600 start_test -performance test/studies/shootout --numtrials=10
echo $DATE
