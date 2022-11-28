{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/ce6aa13369b667ac2542593170993504932eb836.tar.gz") {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python39.withPackages (p: with p; [
      black
      isort
      virtualenv
      pip
      setuptools
      libsass
    ]))
    libsass
    bash
  ];
  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    python3 -m venv .build/venv
    # run ./manage.py compilescss here (uses python39Packages.libsass)
    #. .build/venv/bin/activate
    export PIP_PREFIX=$(pwd)/.build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
    python3 -m pip --quiet install -r requirements.txt
  '';
}
