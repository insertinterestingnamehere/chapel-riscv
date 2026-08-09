# HiFive Unmatched

The HiFive Unmatched is not particularly performant. Compiling Chapel and LLVM
would likely take a very long time. As such, the strategy taken here is to
cross compile Chapel from a more powerful x86_64 host. NixOS was used on both
the x86_64 host and the Unmatched host.

A nice benefit of using Nix is that it has a heavy focus on reproducibility
which should make it straightforward to reproduce the results or audit the
procedure. In order to reproduce the compiled Chapel RiscV binaries and related
libraries, an x86_64 server is needed that is either running NixOS or that has
the Nix package manager installed. Executing the build using Nix will compile a
complete supporting cross compiling environment which may take a while.

It may easiest to reproduce these results on an HiFive Unmatched host running
NixOS. However, as Nix binaries explicitly refer to all of their dependencies
by hash, it should also be possible to run the cross compiled Chapel binary on
other operating systems such as Ubuntu if desired.

With Nix available, Chapel can be compiled using an appropriate Nix expression.
There is an existing project to create a Nix expression to compile Chapel -
[nix-chapel](https://github.com/twesterhout/nix-chapel). That project does not
support cross-compiling, however. So, the necessary support was added in a fork
- https://github.com/DaGenix/nix-chapel, specifically commit
e78454ae14d4b8fd0e9f0610c4a43485809d6ed5. For ease of use, the necessary files
have been copied into the "nix/" subdirectory.

Some changes had to be made to the Chapel repository in order to get the tests
to run on NixOS. The changes are available in a fork of the Chapel repository -
https://github.com/DaGenix/chapel, specifically commit
816095fe1f31bd3b9cd51ef22b77c85c47dabc91). These patches have also been
included in the `patches` directory. These patches should apply on top of
Chapel commit ef6f51e04354ff39c8fe07f87e708454057104d0. The changes are:

* Check in the run.sh script
* Update the shebang lines of some of the PREEXEC scripts to work on NixOS
* Increase the test timeout

## Procedure for running the Chapel Tests

1. Build Chapel from an x86_host for a RiscV64 machine (specifically
   targeting the sifive-u74 CPU). From the `nix` directory, run:

   ```
   nix build .#legacyPackages.x86_64-linux.pkgsCross.riscv64.chapel_hifive_unmatched_llvm_21
   ```

   or

   ```
   nix build .#legacyPackages.x86_64-linux.pkgsCross.riscv64.chapel_hifive_unmatched_llvm_22
   ```

   depending on if you want to build with LLVM 21 or 22.

2. Observe the output name of the nix build by using the command:

   ```
   readlink result
   ```

   For LLVM 21, this should produce the value: `/nix/store/gnjiazvvxw32d3g5anmjp32hrw37nqki-chapel-riscv64-unknown-linux-gnu-2.9.0`.

   For LLVM 22, it should be: `/nix/store/542ny0v883m33knp26gilvkr1xpn7wh9-chapel-riscv64-unknown-linux-gnu-2.9.0`.

3. Copy chapel and its dependencies to the HiFive Unmatched machine:

   ```
   nix-copy-closure --to USERNAME@UNMATCHED_HOST result/
   ```

4. Clone the Chapel repository commit ef6f51e04354ff39c8fe07f87e708454057104d0 and apply
   the patches in the `patches` directory (Or clone the fork).

5. Make the venv:

   ```
   make test-venv
   ```

6. Symlinks must be created in the Chapel source directory that point to our
   cross compiled Chapel build. This can be done with the following commands.
   Note the same hash value from Step 2.

   ```
   mkdir -p bin/linux64-riscv64/
   ln -sf /nix/store/gnjiazvvxw32d3g5anmjp32hrw37nqki-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/chpl bin/linux64-riscv64/chpl
   ln -sf /nix/store/gnjiazvvxw32d3g5anmjp32hrw37nqki-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/printchplenv util/printchplenv
   ```

   or

   ```
   mkdir -p bin/linux64-riscv64/
   ln -sf /nix/store/542ny0v883m33knp26gilvkr1xpn7wh9-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/chpl bin/linux64-riscv64/chpl
   ln -sf /nix/store/542ny0v883m33knp26gilvkr1xpn7wh9-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/printchplenv util/printchplenv
   ```

   depending on LLVM version.

7. Run tests:

   ```
   CHPL_LLVM=system ./run.sh
   ```

## Procedure for running the ChOp test

1. Compile Chapel as above

2. Clone the ChOp repository, commit 2e26c2fb4d3c680c98991128046bdcb1022869f6

3. Copy the benchmark script (ChOp_build_and_bench.sh) from
   https://github.com/insertinterestingnamehere/chapel-riscv/tree/main commit
   db1e4c2bd3948d60019d31f04e686f1c8b6e63b9. Make this file executable and
   place this file in the root of the ChOp directory.

4. Add Chapel to the PATH:

   For LLVM 21:

   ```
   export PATH=/nix/store/gnjiazvvxw32d3g5anmjp32hrw37nqki-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/:"$PATH"
   ```

   or, for LLVM 22:

   ```
   export PATH=/nix/store/542ny0v883m33knp26gilvkr1xpn7wh9-chapel-riscv64-unknown-linux-gnu-2.9.0/bin/:"$PATH"
   ```

5. Run the test:

   ```
   ./ChOp_build_and_bench.sh
   ```

