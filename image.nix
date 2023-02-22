{ pkgs }:
pkgs.dockerTools.pullImage {
  imageName = "nyiyui/ctf";
  imageDigest = "sha256:3a1e96e4b7b7b52886f39bd2c97b534b4d407eb9be310fc4940902d20b395aeb";
  sha256 = "1nyy2a3s51mim2d8gsz6hbsc8kdmvi7wv2ylkdbzd4n40w30h1i3";
  finalImageName = "nyiyui/ctf";
  finalImageTag = "v0a";
}
