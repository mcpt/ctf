#!/usr/bin/env bash

docker build -t ctf2 .
hash=$(docker save ctf2 | nix-hash --flat --type sha256 --base32 /dev/stdin)
docker rmi ctf2

echo $hash > image-hash
cat > image.nix << EOF
pkgs.dockerTools.pullImage {
  imageName = "nyiyui/ctf";
  imageDigest = "sha256:3a1e96e4b7b7b52886f39bd2c97b534b4d407eb9be310fc4940902d20b395aeb";
  sha256 = "$hash";
}
EOF
nix-shell -p nix-prefetch-docker --run 'nix-prefetch-docker nyiyui/ctf v0a --quiet'
