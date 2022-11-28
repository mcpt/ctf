{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/ce6aa13369b667ac2542593170993504932eb836.tar.gz") {} }:

let
  packages = python-packages: with python-packages; [
    black
    isort
    virtualenv
    pip
    setuptools
  ];
  my-python = pkgs.python39.withPackages packages;
in
pkgs.mkShell {
  buildInputs = with pkgs; [ my-python bash ];
  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    python3 -m venv .build/venv
    . .build/venv/bin/activate
    export PIP_PREFIX=$(pwd)/.build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
