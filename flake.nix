{
  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/nixos-22.11;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils, ... }@attrs: flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (system: let
    pkgs = nixpkgs.legacyPackages.${system};
    add-setuptools = super: name: {
      ${name} = super.${name}.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
        }
      );
    };
    nixosLib = import (nixpkgs + "/nixos/lib") { inherit system; };
    common = {
      projectDir = self;
      overrides = pkgs.poetry2nix.defaultPoetryOverrides.extend
        (self: super:
          (add-setuptools super "django-bootstrap5")
          // (add-setuptools super "django-sass-processor")
          // (add-setuptools super "uwsgi")
        );
    };
    autologin = { ... }: { services.getty.autologinUser = "root"; };
  in {
    devShells.default = (pkgs.poetry2nix.mkPoetryEnv common // {
      editablePackageSources = {
        ctf = ./.;
      };
    }).env.overrideAttrs (prev: {
      buildInputs = [ pkgs.python310 pkgs.poetry ];
    });
  });
}
