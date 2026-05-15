#!/usr/bin/env bash
#SBATCH -o compile.out
#SBATCH -e compile.err
#SBATCH -t 47:55:00
#SBATCH -p risc5

export CHPL_COMM=none
export CHPL_TARGET_MEM=mimalloc
export CHPL_HOST_MEM=mimalloc
export CHPL_LLVM=system
export CHPL_LLVM_TARGETS_TO_BUILD=host
export CHPL_TARGET_CPU=sifive-u74

./configure --prefix=/home/diehlpk/opt/chapel

make -j32
