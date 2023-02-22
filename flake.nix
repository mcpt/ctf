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
        );
    };
    autologin = { ... }: { services.getty.autologinUser = "root"; };
  in {
    devShells.default = (pkgs.poetry2nix.mkPoetryEnv common // {
      editablePackageSources = {
        ctf = ./.;
      };
    }).env.overrideAttrs (prev: {
      buildInputs = [ pkgs.python310 ];
    });
    packages.default = pkgs.poetry2nix.mkPoetryApplication common // { };
    packages.image = import ./image.nix { inherit pkgs; };
    checks.all = nixosLib.runTest {
      name = "all";
      hostPkgs = pkgs;
      nodes.default = { pkgs, ... }: {
        imports = [ autologin self.outputs.nixosModules.${system}.default ];
        youcopter.services.uwsgi = {
          enable = true;
        };
      };
      testScript = ''
        start_all()
        default.wait_for_unit('uwsgi.service')
      '';
    };
    checks.fastrouter = let
      user = "youcopter-uwsgi";
      group = "youcopter-uwsgi";
      worker = { pkgs, ... }: {
        imports = [ autologin ];
        users.groups.${user} = {};
        users.users.${group} = {
          isSystemUser = true;
          description = "Youcopter uWSGI";
          group = group;
        };
        services.uwsgi = {
          enable = true;
          plugins = [ "python3" ];
          instance.type = "emperor";
          instance.vassals.youcopter = {
            type = "normal";
            pythonPackages = lib: [ self.outputs.packages.${system}.default ];
            subscribe-to = "main:7000:example.net";
            master = true;
            vacuum = true;

            uid = user;
            gid = group;

            plugins = [ "python3" ];

            module = "mCTF.wsgi:application";
            env = [ "DJANGO_SETTINGS_MODULE=mCTF.settings" ];
          };
        };
      };
    in nixosLib.runTest {
      name = "fastrouter";
      hostPkgs = pkgs;
      nodes.worker1 = worker;
    };
    nixosModules.default = { config, lib, pkgs, ... }: with lib; with types; let
      cfg = config.youcopter.services.uwsgi;
      user = "youcopter-uwsgi";
      group = "youcopter-uwsgi";
    in {
      options.youcopter.services.uwsgi = {
        enable = mkEnableOption "Youcopter (mCTF) barebones uwsgi: CTF platform supporting multiple parallel contests";
        config = mkOption {
          type = submodule {
            options = {
            };
          };
        };
      };
      config = mkIf cfg.enable {
        users.groups.${user} = {};
        users.users.${group} = {
          isSystemUser = true;
          description = "Youcopter uWSGI";
          group = group;
        };
        services.uwsgi = {
          enable = true;
          plugins = [ "python3" ];
          instance.type = "emperor";
          instance.vassals.youcopter = {
            type = "normal";
            pythonPackages = lib: [ self.outputs.packages.${system}.default ];
            http = "127.0.0.1:8080";
            master = true;
            vacuum = true;

            uid = user;
            gid = group;

            plugins = [ "python3" ];

            module = "mCTF.wsgi:application";
            env = [ "DJANGO_SETTINGS_MODULE=mCTF.settings" ];
          };
        };
      };
    };
  });
}
