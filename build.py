#!/usr/bin/env python3

from argparse import ArgumentParser
from os import chdir, makedirs
from os.path import dirname, isdir, realpath
import shutil
import subprocess
import tarfile
from tempfile import NamedTemporaryFile


def command(cmd, redirect=None):
    if redirect is None:
        subprocess.check_call(cmd)
    else:
        with NamedTemporaryFile() as f:
            subprocess.check_call(cmd, stdout=f)
            d = realpath(dirname(redirect))
            if not isdir(d):
                makedirs(d)
            shutil.copy(f.name, redirect)


def print_cyan(*args):
    from sys import stdout
    stdout.write("\x1b[1;36m")
    print(*args, end="")
    stdout.write("\x1b[0m\n")


def cargo(subcmd, mode="debug"):
    flags = []
    if mode == "release":
        flags.append("--release")
    command(["cargo", "-q", subcmd] + flags)


oftb_exec = "target/release/oftb"


def oftb(args, redirect=None):
    command([oftb_exec, "-v"] + args, redirect=redirect)


def compile(pkg_dir, bin_name):
    print_cyan("compile", bin_name)
    oftb(["compile", "--std", "ministd", pkg_dir, bin_name])


def interpret(pkg_dir, bin_name, *args, redirect=None):
    print_cyan("interpret", bin_name, *args)
    bin_path = "{}/build/{}.ofta".format(pkg_dir, bin_name)
    oftb(["interpret", bin_path] + list(args), redirect=redirect)


def run(pkg_dir, bin_name, *args, redirect=None):
    print_cyan("run", bin_name, *args)
    args = ["run", "--std", "ministd", pkg_dir, bin_name] + list(args)
    oftb(args, redirect=redirect)


def run_with_macros(pkg_dir, bin_name, *args, redirect=None):
    bin_path = "{}/build/{}.ofta".format(pkg_dir, bin_name)
    interpret("macro-expander", "oftb-macro-expander", "ministd", pkg_dir,
              bin_name, redirect=bin_path)
    interpret(pkg_dir, bin_name, *args, redirect=redirect)


def build_oftb():
    print_cyan("build oftb")
    cargo("check")
    cargo("doc")
    cargo("build", mode="release")


def bootstrap():
    run("macro-expander", "make-prelude", "ministd",
        redirect="ministd/src/prelude.oft")
    run("macro-expander", "make-env", "ministd",
        redirect="macro-expander/src/interpreter/env.oft")
    compile("macro-expander", "oftb-macro-expander")
    run_with_macros("examples/structure", "structure")


def make_archive():
    with tarfile.open("oftb.tar.gz", "x:gz") as tar:
        tar.add(oftb_exec, arcname="oftb")
        tar.add("macro-expander")
        tar.add("ministd")


if __name__ == "__main__":
    chdir(dirname(__file__))
    parser = ArgumentParser()
    parser.add_argument("--no-oftb-build", action="store_true")
    parser.add_argument("--use-system-oftb", action="store_true")
    args = parser.parse_args()
    if args.use_system_oftb:
        oftb_exec = "oftb"
    elif not args.no_oftb_build:
        build_oftb()
    bootstrap()
    make_archive()
