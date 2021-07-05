#!/usr/bin/env python3
# Copyright (c) 2020-2021, Videonetics Technology Pvt Ltd. All rights reserved.
# mypy: ignore-errors

import argparse
import glob
import logging
import os
import pathlib
import platform
import shutil
import signal
import subprocess
import sys
import time
import traceback
import zipfile
from distutils.dir_util import copy_tree


def get_cwd() -> str:
    cwd = os.path.dirname(os.path.realpath(__file__))
    if not cwd:
        cwd = os.getcwd()
    return cwd


FLAGS = None


def log(msg, force=False):
    if force or not FLAGS.quiet:
        try:
            print(msg, file=sys.stderr)
        except Exception:
            print("<failed to log>", file=sys.stderr)


def log_verbose(msg):
    if FLAGS.verbose:
        log(msg, force=True)


def fail(msg):
    fail_if(True, msg)


def target_platform():
    if FLAGS.target_platform is not None:
        return FLAGS.target_platform
    return platform.system().lower()


def fail_if(p, msg):
    if p:
        print("error: {}".format(msg), file=sys.stderr)
        sys.exit(1)


def mkdir(path):
    log_verbose("mkdir: {}".format(path))
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def rmdir(path):
    log_verbose("rmdir: {}".format(path))
    shutil.rmtree(path, ignore_errors=True)


def cpdir(src, dest):
    log_verbose("cpdir: {} -> {}".format(src, dest))
    copy_tree(src, dest, preserve_symlinks=1)


def get_version():
    with open("vrpc/VERSION", "r") as vfile:
        FLAGS.version = vfile.readline().strip()
    log("version: {}".format(FLAGS.version))


def reset_version():
    # Determine the versions from VERSION file.
    reset_version = "0.0.0"
    filename = os.path.join(get_cwd(), "vrpc/VERSION")
    with open(filename, "w") as vfile:
        vfile.writelines(f"{reset_version}")
    lines = []
    filename = os.path.join(get_cwd(), ".bumpversion.cfg")
    with open(filename, "r") as vfile:
        lines = vfile.readlines()
    for i, line in enumerate(lines):
        if line.startswith("current_version = "):
            lines[i] = f"current_version = {reset_version}\n"
    with open(filename, "w") as vfile:
        vfile.writelines(lines)

    get_version()
    log("version: {}".format(FLAGS.version))


def bump_to_version(minor: bool = False, major: bool = False, reset: bool = False):
    runarguments = ["bump2version", "--allow-dirty"]
    if reset:
        reset_version()
        runarguments += ["patch"]
    elif major:
        runarguments += ["major"]
    elif minor:
        runarguments += ["minor"]
    else:
        runarguments += ["patch"]
    # runarguments = ['which', 'bump2version']
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "bump_to_version failed")
        get_version()
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        fail("bump_to_version failed")


def remove_file_or_dir(inp_path, recursive=False):
    """param <path> could either be relative or absolute."""
    path = str(pathlib.Path(inp_path).absolute())
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        glob_list = glob.glob(path, recursive=recursive)
        if len(glob_list) > 0:
            for name in glob_list:
                log_verbose(name)
                if os.path.isfile(name) or os.path.islink(name):
                    os.remove(name)  # remove the file
                elif os.path.isdir(name):
                    shutil.rmtree(name)  # remove dir and all contains


def remove_cythonize():
    remove_file_or_dir(FLAGS.dist_dir)


def remove_session_dir():
    remove_file_or_dir(FLAGS.session_dir)


def remove_persistent_dir():
    remove_file_or_dir(FLAGS.persistent_dir)


def clean_cythonize():
    remove_file_or_dir("build")
    remove_file_or_dir(f"{FLAGS.base_dir}.egg-info")
    remove_file_or_dir(f"{FLAGS.base_dir}/**/*.c", recursive=True)
    remove_file_or_dir(f"{FLAGS.base_dir}/**/*.o", recursive=True)
    # remove_file_or_dir(f'{FLAGS.base_dir}/**/*.so', recursive=True)

    # rm -rf *.egg-info
    # find . -name "*.c" -type f -delete
    # find . -name "*.o" -type f -delete
    # find . -name "*.so" -type f -delete


def zip_dir(dir_name, filename):
    """zipper"""
    with zipfile.ZipFile(
        filename, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zip:
        for root, _, files in os.walk(dir_name):
            for f in files:
                rel_path = os.path.join(os.path.relpath(root, dir_name), f)
                abs_path = os.path.join(root, f)
                zip.write(abs_path, rel_path)


def wheel_remove_source_files():
    for filename in glob.glob(os.path.join(FLAGS.dist_dir, "*.whl")):
        name = os.path.splitext(os.path.basename(filename))[0]
        try:
            dir_name = os.path.join(FLAGS.dist_dir, name)
            os.mkdir(dir_name)
            log_verbose(f"Extracting files in {dir_name}")
            with zipfile.ZipFile(filename) as zip:
                zip.extractall(path=dir_name)

            file_list = glob.glob(os.path.join(dir_name, "**/*.py"), recursive=True)
            file_list.extend(
                glob.glob(os.path.join(dir_name, "**/*.c"), recursive=True)
            )
            for filename1 in file_list:
                if not filename1.endswith("__init__.py"):
                    if os.path.isfile(filename1) or os.path.islink(filename1):
                        os.remove(filename1)  # remove the file
            zip_dir(dir_name, filename)
            shutil.rmtree(dir_name)

        except zipfile.BadZipfile:
            print("BAD ZIP: " + filename)

        log(filename)


def do_cythonize():
    clean_cythonize()
    remove_cythonize()
    # runarguments = [sys.executable, 'setup.py', 'bdist_wheel', '--exclude_source_files']
    runarguments = [sys.executable, "setup.py", "bdist_wheel", "-d", FLAGS.dist_dir]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        wheel_remove_source_files()
        clean_cythonize()
        fail_if(p.returncode != 0, "do_cythonize failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_cythonize failed")


def do_mypy_test():
    runarguments = [sys.executable, "-m", "mypy", FLAGS.base_dir]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "do_mypy_test failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_mypy_test failed")


def do_sort_import():
    runarguments = [sys.executable, "-m", "isort", FLAGS.base_dir]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "do_sort_import failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_sort_import failed")


def do_format_black():
    runarguments = [sys.executable, "-m", "black", FLAGS.base_dir]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "do_format_black failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_format_black failed")


def do_format_yapf():
    runarguments = [
        sys.executable,
        "-m",
        "yapf",
        "--in-place",
        "--recursive",
        FLAGS.base_dir,
    ]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "do_format_yapf failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_format_yapf failed")


def run_module():
    runarguments = [sys.executable, "-m", "vrpc"]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        logging.info("Running module")
        time.sleep(10)
        logging.info("Sending stop signal")
        p.send_signal(signal.SIGTERM)
        p.wait()
        fail_if(p.returncode != 0, f"run_module failed {p.returncode}")
    except Exception:
        logging.error(traceback.format_exc())
        fail("run_module failed")


def generate_proto_code1():
    proto_interface_dir = "vrpc/data_models/interfaces"
    out_folder = "vrpc/data_models"
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    subprocess.check_call(
        ["protoc"]
        + protos
        + ["--python_out", out_folder, "--proto_path", proto_interface_dir]
    )


def generate_proto_code():
    proto_interface_dir = "vrpc/data_models/interfaces"
    out_folder = "vrpc/data_models"
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    subprocess.check_call(
        ["protoc"]
        + protos
        + ["--python_betterproto_out", out_folder, "--proto_path", proto_interface_dir]
    )


def generate_proto_code2():
    proto_interface_dir = "vrpc/data_models/interfaces"
    out_folder = "vrpc/data_models"
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    subprocess.check_call(
        ["python", "-m", "grpc.tools.protoc"]
        + protos
        + ["--python_betterproto_out", out_folder, "--proto_path", proto_interface_dir]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    group_qv = parser.add_mutually_exclusive_group()
    group_qv.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        required=False,
        help="Disable console output.",
    )
    group_qv.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        help="Enable verbose output.",
    )

    parser.add_argument(
        "--enable-logging", action="store_true", required=False, help="Enable logging."
    )
    parser.add_argument(
        "--enable-stats",
        action="store_true",
        required=False,
        help="Enable statistics collection.",
    )

    FLAGS = parser.parse_args()
    FLAGS.cwd = get_cwd()
    FLAGS.dist_dir = os.path.join(get_cwd(), "dist")
    FLAGS.base_dir = "vrpc"
    FLAGS.session_dir = os.path.join(get_cwd(), "session")
    FLAGS.persistent_dir = os.path.join(get_cwd(), "persistent")
    # Determine the versions from VERSION file.
    get_version()
    remove_session_dir()
    remove_persistent_dir()
    generate_proto_code()
    do_sort_import()
    do_format_black()
    do_format_yapf()
    # run_module()
    do_mypy_test()
    # bump_to_version()
    # do_cythonize()
