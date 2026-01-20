{ pkgs ? import <nixpkgs> {} }:
with pkgs; mkShell {
  packages = [
    gnumake
  ];
}
