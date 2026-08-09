# Check https://chapel-lang.org/docs/usingchapel/prereqs.html#readme-prereqs to see the currently supported LLVM versions
# Check https://search.nixos.org/packages?channel=unstable&from=0&size=50&sort=relevance&type=packages&query=llvmPackages to see which LLVM versions are available in Nixpkgs.
{ bash
, cmake
, coreutils
, fetchFromGitHub
, file
, gcc
, glibc
, gmp
, gnum4
, gnumake
, lib
, libunwind
, llvmPackages
, makeWrapper
, patchelf
, perl
, pkg-config
, pmix
, python3
, python3Packages
, rdma-core
, removeReferencesTo
, stdenv
, which
, xz
, buildPackages
, pkgsBuildHost
, compiler ? "llvm"
, settings ? { }
}:

assert compiler == "llvm" || compiler == "gnu";

let
  pycparser = python3Packages.buildPythonPackage {
    pname = "pycparser";
    version = "2.20";
    pyproject = false;
    src = fetchFromGitHub {
      owner = "eliben";
      repo = "pycparser";
      rev = "release_v2.20";
      hash = "sha256-M2Col80YezCyRpKSKBPav8HrLhfmbzLxAIpVz0ULBYg=";
    };
    doCheck = false;
  };
  pycparserext = python3Packages.buildPythonPackage {
    pname = "pycparserext";
    version = "2020.1";
    pyproject = false;
    src = fetchFromGitHub {
      owner = "inducer";
      repo = "pycparserext";
      rev = "6b9db4a17130bd90a4c8e44d07f39ba9cc36c6d1";
      hash = "sha256-PYfYOukddeo7SN6B9GYNY2mj3S1Dhk0ONw8ycOoYPWA=";
    };
    propagatedBuildInputs = with python3Packages; [ pycparser ply ];
  };

  targetTriple = if (stdenv.buildPlatform != stdenv.hostPlatform) then stdenv.hostPlatform.config else "";
  targetTriplePrefix = if (stdenv.buildPlatform != stdenv.hostPlatform) then "${targetTriple}-" else "";

  commonSettings = {
    CHPL_GMP = "none";
    CHPL_RE2 = "bundled";
    CHPL_UNWIND = "none";
    CHPL_LAUNCHER = "none";
    CHPL_TARGET_MEM = "jemalloc";
    CHPL_TARGET_CPU = "none";
  } // lib.optionalAttrs llvmPackages.stdenv.isLinux {
    PMI_HOME = "${pmix}";
  };

  llvmSpecificSettings = {
    CC = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}cc";
    CXX = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}c++";
    CHPL_LLVM = "system";
    CHPL_LLVM_SUPPORT = "system";
    # TODO: This is an ugly hack
    CHPL_LLVM_CONFIG = "${pkgsBuildHost.llvmPackages.llvm.dev}/bin/llvm-config";
    CHPL_HOST_COMPILER = "llvm";
    # TODO: This is an ugly hack
    CHPL_HOST_CC = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}clang";
    CHPL_HOST_CXX = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}clang++";
    CHPL_TARGET_CC = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}clang";
    CHPL_TARGET_CXX = "${pkgsBuildHost.llvmPackages.clang}/bin/${targetTriplePrefix}clang++";
  };

  gnuSpecificSettings = {
    CC = "${gcc}/bin/cc";
    CXX = "${gcc}/bin/c++";
    CHPL_LLVM = "none";
    CHPL_LLVM_SUPPORT = "system";
    CHPL_HOST_COMPILER = "gnu";
    CHPL_HOST_CC = "${gcc}/bin/gcc";
    CHPL_HOST_CXX = "${gcc}/bin/g++";
    CHPL_TARGET_CC = "${gcc}/bin/gcc";
    CHPL_TARGET_CXX = "${gcc}/bin/g++";
  };

  chplSettings = commonSettings // (if compiler == "llvm" then llvmSpecificSettings else gnuSpecificSettings) // settings;
  chplSettingsOnHost = chplSettings // {
    CC = "${llvmPackages.clang}/bin/clang";
    CXX = "${llvmPackages.clang}/bin/clang++";
    CHPL_LLVM_CONFIG = "${llvmPackages.llvm.dev}/bin/llvm-config";
    CHPL_HOST_CC = "${llvmPackages.clang}/bin/clang";
    CHPL_HOST_CXX = "${llvmPackages.clang}/bin/clang++";
    CHPL_TARGET_CC = "${llvmPackages.clang}/bin/clang";
    CHPL_TARGET_CXX = "${llvmPackages.clang}/bin/clang++";
  };
  chplStdenv = if compiler == "llvm" then llvmPackages.stdenv else stdenv;

  chplBuildEnv = lib.concatStringsSep " " (lib.mapAttrsToList (k: v: "${k}='${v}'") chplSettings);

  chplPrefix = (if chplStdenv.isLinux then "linux64-" else "darwin-") + (if chplStdenv.isx86_64 then "x86_64" else "arm64");

  wrapperArgs = lib.concatStringsSep " " ([
    "--prefix PATH : '${lib.makeBinPath [coreutils gnumake pkg-config python3 which]}'"
    "--set CHPL_HOME $out"
  ]
  ++ (lib.mapAttrsToList (k: v: "--set-default ${k} '${v}'") chplSettingsOnHost)
  ++ lib.optionals (chplSettings.CHPL_UNWIND == "system" && !chplStdenv.isDarwin) [ "--prefix PKG_CONFIG_PATH : '${libunwind.dev}/lib/pkgconfig'" ]);

  compilerSpecificWrapperArgs = lib.concatStringsSep " " ([ "--add-flags '-L ${xz.out}/lib'" ]
  ++ lib.optionals (chplSettings.CHPL_GMP == "system") [ "--add-flags '-L ${gmp}/lib'" "--prefix PKG_CONFIG_PATH : '${gmp.dev}/lib/pkgconfig'" ]
  ++ lib.optionals (!chplStdenv.isDarwin && compiler == "llvm") [
    "--add-flags '--ccflags -idirafter --ccflags ${llvmPackages.clang-unwrapped.lib}/lib/clang/${lib.versions.major llvmPackages.clang.version}/include'"
    "--add-flags '--ccflags -idirafter --ccflags ${llvmPackages.clang}/resource-root/include'"
    "--add-flags '--ccflags -idirafter --ccflags ${llvmPackages.bintools.libc.dev}/include'"
  ]
  ++ lib.optionals (!chplStdenv.isDarwin && compiler == "gnu") [ "--add-flags '-I ${chplStdenv.cc.libc.dev}/include'" ]
  ++ lib.optionals chplStdenv.isDarwin [ "--add-flags '-I ${chplStdenv.libc}/include'" ]);
in
chplStdenv.mkDerivation rec {
  pname = "chapel";
  version = "2.9.0";
  src = fetchFromGitHub {
    owner = "chapel-lang";
    repo = "chapel";
    rev = "ef6f51e04354ff39c8fe07f87e708454057104d0";
    hash = "sha256-Dc4vTraSwKggV6MxE+2NZEwLCqGioePs5/w5/VAoQ7I=";
  };

  outputs = [ "out" "third_party" ];

  c2chapel-fake-headers = fetchFromGitHub {
    owner = "eliben";
    repo = "pycparser";
    rev = "0055facfb5b5289ce8ef2ef12b18e34a223f9d20";
    hash = "sha256-M2Col80YezCyRpKSKBPav8HrLhfmbzLxAIpVz0ULBYg=";
  };

  passthru.llvmPackages = llvmPackages;

  postPatch = ''
    # We need to patch the scripts that will be installed for both the build and host systems. So, we save
    # a copy of the scripts patched for the host sytem before patching the scripts for the
    # build system.
    mkdir host-patched-scripts
    cp util/printchplenv util/config/compileline tools/c2chapel/c2chapel.py host-patched-scripts/
    patchShebangs --host host-patched-scripts/

    patchShebangs --build configure
    patchShebangs --build util/printchplenv
    patchShebangs --build util/config/compileline
    patchShebangs --build util/test/checkChplInstall
    patchShebangs --build tools/c2chapel/c2chapel.py

    export CHPL_DONT_BUILD_CHPLDOC_VENV=1
    export CHPL_DONT_BUILD_TEST_VENV=1
    export CHPL_DONT_BUILD_C2CHAPEL_VENV=1

    # Needed until https://github.com/chapel-lang/chapel/issues/24128 is resolved
    substituteInPlace third-party/Makefile \
      --replace-fail 'cd chpl-venv && $(MAKE) c2chapel-venv' \
                     'if [ -z "$$CHPL_DONT_BUILD_C2CHAPEL_VENV" ]; then cd chpl-venv && $(MAKE) c2chapel-venv; fi'
    # tools/c2chapel/Makefile \
    #   --replace 'c2chapel-venv $(FAKES)' '$(FAKES)'

    # This is essentially what the $(FAKES) target in the Makefile does, but
    # we use $${c2chapel-fake-headers} instead of downloading the archive from
    # the internet
    pushd tools/c2chapel
    mkdir -p install/fakeHeaders
    cp --no-preserve=mode -r ${c2chapel-fake-headers}/utils/fake_libc_include/* install/fakeHeaders/
    ./utils/fixFakes.sh install/fakeHeaders utils/custom.h
    mkdir -p install/fakeHeaders/utils
    cp utils/custom.h install/fakeHeaders/utils/
    popd

    substituteInPlace util/chplenv/chpl_llvm.py \
      --replace-warn 'if macro in out' 'if False'

    substituteInPlace third-party/hwloc/Makefile \
      --replace-fail --disable-rsmi "--disable-rsmi --host=${targetTriple}"

    substituteInPlace third-party/libunwind/Makefile \
      --replace-fail --disable-zlibdebuginfo "--disable-zlibdebuginfo --host=${targetTriple}"

    # HACK ALERT
    substituteInPlace util/buildRelease/install.sh \
      --replace-fail 'VERS=`$CHPL_HOME/bin/$CHPL_BIN_SUBDIR/chpl --version`' VERS=${version}

    # HACK ALERT
    substituteInPlace runtime/etc/Makefile.include \
      --replace-fail '$(CXX)' ${buildPackages.stdenv.cc}/bin/c++

  '' + lib.optionalString (stdenv.buildPlatform != stdenv.hostPlatform) ''
    substituteInPlace third-party/gmp/Makefile \
      --replace-fail '$(CHPL_MAKE_HOST_CC)' ${buildPackages.stdenv.cc}/bin/cc \
      --replace-fail 'CHPL_GMP_CFG_OPTIONS += $(CHPL_GMP_MORE_CFG_OPTIONS)' 'CHPL_GMP_CFG_OPTIONS += $(CHPL_GMP_MORE_CFG_OPTIONS) --host=${targetTriple}' \
      --replace-fail 'GMP_CROSS_COMPILED=no' 'GMP_CROSS_COMPILED=yes'
  '';

  configurePhase = ''
    export ${chplBuildEnv}
    ./configure --chpl-home=$out
  '';

  buildPhase = ''
    make -j$NIX_BUILD_CORES
    make -j$NIX_BUILD_CORES c2chapel
  '';

  enableParallelBuilding = true;

  postInstall = ''
    # The scripts that were installed were patched for the build system. We need to
    # replace them with scripts patched for the host system.
    cp host-patched-scripts/printchplenv $out/util/printchplenv
    cp host-patched-scripts/compileline $out/util/config/compileline
    cp host-patched-scripts/c2chapel.py $out/tools/c2chapel/c2chapel.py 

    mkdir -p $third_party
    cp -v -r $out/third-party/gasnet $third_party
    find $third_party -type d -name "include" -exec rm -r {} +
    find $third_party -type d -name "lib" -exec rm -r {} +
    find $third_party -type d -name "share" -exec rm -r {} +
    find $third_party -type f -name "Makefile*" -exec rm {} +

    mkdir -p $out/tools/c2chapel
    cp tools/c2chapel/c2chapel* $out/tools/c2chapel/
    cp -r tools/c2chapel/install $out/tools/c2chapel/

    makeWrapper $out/tools/c2chapel/c2chapel.py $out/bin/c2chapel \
      --prefix PYTHONPATH : "${pycparser}/${python3.sitePackages}" \
      --prefix PYTHONPATH : "${pycparserext}/${python3.sitePackages}"

    wrapProgram $out/util/printchplenv \
      ${wrapperArgs}

    ln -s $out/util/printchplenv $out/bin/

    makeWrapper $out/bin/*/chpl $out/bin/chpl \
      ${wrapperArgs} \
      ${compilerSpecificWrapperArgs}
  '' + lib.optionalString chplStdenv.isLinux ''
    substitute ${./chapel-fixup-binary.sh} $out/bin/chapelFixupBinary \
      --subst-var "shell" \
      --subst-var "out" \
      --subst-var "third_party" \
      --replace-fail "@removeReferencesTo@" "${removeReferencesTo}" \
      --replace-fail "@llvmPackages.clang@" "${llvmPackages.clang}" \
      --replace-fail "@llvmPackages.clang-unwrapped.lib@" "${llvmPackages.clang-unwrapped.lib}" \
      --replace-fail "@llvmPackages.llvm.dev@" "${llvmPackages.llvm.dev}" \
      --replace-fail "@llvmPackages.bintools.libc.dev@" "${llvmPackages.bintools.libc.dev}" \
      --replace-fail "@chplStdenv.cc.libc.dev@" "${chplStdenv.cc.libc.dev}"
    chmod +x $out/bin/chapelFixupBinary

    # libChplFrontendShared.so contains a reference to lib/compiler/linux64-x86_64 in its RPATH.
    # This folder contains libChplFrontend.so, but libChplFrontend.so has also
    # been installed to $out/lib/compiler/linux64-x86_64. Remove the temporary
    # build folder and instead add $ORIGIN to RPATH
    rm -r lib/compiler/linux64-x86_64
    patchelf --add-rpath '$ORIGIN' $out/lib/compiler/linux64-x86_64/libChplFrontendShared.so
  '';

  buildInputs =
    [ llvmPackages.llvm llvmPackages.libclang.dev bash python3 ]
    ++ lib.optionals (chplSettings.CHPL_UNWIND == "system") [ libunwind ]
    ++ lib.optionals (chplSettings.CHPL_GMP == "system") [ gmp ]
    ++ lib.optionals (compiler == "llvm") [ llvmPackages.clang ]
    ++ lib.optionals chplStdenv.isLinux [ pmix rdma-core ];

  depsBuildBuild = [
    llvmPackages.bintools
  ];

  nativeBuildInputs = [
    bash
    cmake
    gnumake
    gnum4
    file
    makeWrapper
    patchelf
    perl
    pkg-config
    python3
    which
    coreutils
  ] ++ lib.optionals (compiler == "llvm") [
    llvmPackages.clang
    glibc.dev
  ] ++ lib.optionals (compiler == "gnu") [
    gcc
  ];

  meta = {
    description = "a Productive Parallel Programming Language";
    homepage = "https://chapel-lang.org/";
  };
}
