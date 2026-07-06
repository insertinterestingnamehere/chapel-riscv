#!/usr/bin/env bash

# build Chapel into an existing conda environment with the following installed:
# python automake autoconf clang=21 clangxx clangdev llvmdev gcc=15 gxx binutils cmake
# note: use conda-forge.
export CHPL_COMM=none
export CHPL_LLVM=system
export CHPL_TARGET_MEM=mimalloc
export CHPL_HOST_MEM=mimalloc
# work around potential conflict between system-wide gmake and conda-installed make
export CHPL_MAKE=make
export MAKE=make
export CHPL_MAKE_MAKE=make
export CC=clang
export CXX=clang++
export CMAKE_PREFIX_PATH="$CONDA_PREFIX"
export MACHINE_TYPE=$(uname -m)
export CFLAGS="-I$CONDA_PREFIX/$MACHINE_TYPE-conda-linux-gnu/sysroot/usr/include -g $CFLAGS"
export CXXFLAGS="-I$CONDA_PREFIX/$MACHINE_TYPE-conda-linux-gnu/sysroot/usr/include -g $CXXFLAGS"
export CPPFLAGS="$CXXFLAGS"
cd chapel
git clean -fdx
git clean -fdX
./configure --prefix="$CONDA_PREFIX"
make -j$(nproc --all)
make install
make test-venv

