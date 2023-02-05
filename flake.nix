{
  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/nixos-22.11;
    flake-utils.url = github:numtide/flake-utils;
    poetry2nix.url = github:nix-community/poetry2nix;
    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix, ... }@attrs: flake-utils.lib.eachSystem [ "x86_64-linux" ] (system: let
    inherit (poetry2nix.legacyPackages.${system}) mkPoetryApplication mkPoetryEnv;
    pkgs = nixpkgs.legacyPackages.${system};
    add-setuptools = super: name: {
      ${name} = super.${name}.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
        }
      );
    };
  in let
    common = {
      projectDir = ./.;
      python = pkgs.python310;
      overrides = pkgs.poetry2nix.defaultPoetryOverrides.extend
        (self: super:
          (add-setuptools super "django-bootstrap5")
          // (add-setuptools super "django-sass-processor")
        );
      editablePackageSources = {
        ctf = ./.;
      };
    };
  in {
    devShells.default = (mkPoetryEnv common).env.overrideAttrs (prev: {
      buildInputs = [ pkgs.python310 ];
    });
  });
}
