{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    ( python3.withPackages (ps: with ps;
    [ requests attrs click pytest ]))
    ];
}
