#!/usr/bin/env python3
# Copyright (c) 2020-2021, Videonetics Technology Pvt Ltd. All rights reserved.
# mypy: ignore-errors

import argparse
import glob
import logging
import os
import pathlib
import platform
from posixpath import join
import shutil
import signal
import subprocess
import sys
import time
import traceback
import venv
import zipfile
from distutils.dir_util import copy_tree
from subprocess import PIPE, Popen
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlretrieve


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
    with open(os.path.join(FLAGS.base_dir, "VERSION"), "r") as vfile:
        FLAGS.version = vfile.readline().strip()
    log("version: {}".format(FLAGS.version))


def reset_version():
    # Determine the versions from VERSION file.
    reset_version = "0.0.0"
    filename = os.path.join(FLAGS.base_dir, "VERSION")
    with open(filename, "w") as vfile:
        vfile.writelines(f"{reset_version}")
    lines = []
    filename = os.path.join(FLAGS.cwd, ".bumpversion.cfg")
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
        os.remove(path)    # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)    # remove dir and all contains
    else:
        glob_list = glob.glob(path, recursive=recursive)
        if len(glob_list) > 0:
            for name in glob_list:
                log_verbose(name)
                if os.path.isfile(name) or os.path.islink(name):
                    os.remove(name)    # remove the file
                elif os.path.isdir(name):
                    shutil.rmtree(name)    # remove dir and all contains


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
    with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip:
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
            file_list.extend(glob.glob(os.path.join(dir_name, "**/*.c"), recursive=True))
            for filename1 in file_list:
                if not filename1.endswith("__init__.py"):
                    if os.path.isfile(filename1) or os.path.islink(filename1):
                        os.remove(filename1)    # remove the file
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
    log("Yapf formatting started")
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        p.wait()
        fail_if(p.returncode != 0, "do_format_yapf failed")
    except Exception:
        logging.error(traceback.format_exc())
        fail("do_format_yapf failed")
    log("Yapf formatting completed")


def run_module():
    runarguments = [sys.executable, "-m", FLAGS.module_name]
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
    proto_interface_dir = f"{FLAGS.base_dir}/data_models/interfaces"
    out_folder = f"{FLAGS.base_dir}/data_models"
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    subprocess.check_call(["protoc"] + protos + ["--python_out", out_folder, "--proto_path", proto_interface_dir])


def generate_proto_code():
    proto_interface_dir = f"{FLAGS.module_name}/data_models/interfaces"
    out_folder = f"{FLAGS.module_name}/data_models"
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    subprocess.check_call(["protoc"] + protos +
                          ["--python_betterproto_out", out_folder, "--proto_path", proto_interface_dir])


class ExtendedEnvBuilder(venv.EnvBuilder):
    """
    This builder installs setuptools and pip so that you can pip or
    easy_install other packages into the created virtual environment.

    :param nodist: If true, setuptools and pip are not installed into the
                   created virtual environment.
    :param nopip: If true, pip is not installed into the created
                  virtual environment.
    :param progress: If setuptools or pip are installed, the progress of the
                     installation can be monitored by passing a progress
                     callable. If specified, it is called with two
                     arguments: a string indicating some progress, and a
                     context indicating where the string is coming from.
                     The context argument can have one of three values:
                     'main', indicating that it is called from virtualize()
                     itself, and 'stdout' and 'stderr', which are obtained
                     by reading lines from the output streams of a subprocess
                     which is used to install the app.

                     If a callable is not specified, default progress
                     information is output to sys.stderr.
    """
    def __init__(self, *args, **kwargs):
        self.nodist = kwargs.pop("nodist", False)
        self.nopip = kwargs.pop("nopip", False)
        self.progress = kwargs.pop("progress", None)
        self.verbose = kwargs.pop("verbose", False)
        super().__init__(*args, **kwargs)

    def post_setup(self, context):
        """
        Set up any packages which need to be pre-installed into the
        virtual environment being created.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        os.environ["VIRTUAL_ENV"] = context.env_dir
        # if not self.nodist:
        #     self.install_setuptools(context)
        # Can't install pip without setuptools
        if not self.nopip and not self.nodist:
            self.install_pip(context)

    def reader(self, stream, context):
        """
        Read lines from a subprocess' output stream and either pass to a progress
        callable (if specified) or write progress information to sys.stderr.
        """
        progress = self.progress
        while True:
            s = stream.readline()
            if not s:
                break
            if progress is not None:
                progress(s, context)
            else:
                if not self.verbose:
                    sys.stderr.write(".")
                else:
                    sys.stderr.write(s.decode("utf-8"))
                sys.stderr.flush()
        stream.close()

    def install_script(self, context, name, url):
        _, _, path, _, _, _ = urlparse(url)
        fn = os.path.split(path)[-1]
        binpath = context.bin_path
        distpath = os.path.join(binpath, fn)
        # Download script into the virtual environment's binaries folder
        urlretrieve(url, distpath)
        progress = self.progress
        if self.verbose:
            term = "\n"
        else:
            term = ""
        if progress is not None:
            progress("Installing %s ...%s" % (name, term), "main")
        else:
            sys.stderr.write("Installing %s ...%s" % (name, term))
            sys.stderr.flush()
        # Install in the virtual environment
        args = [context.env_exe, fn]
        p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=binpath)
        t1 = Thread(target=self.reader, args=(p.stdout, "stdout"))
        t1.start()
        t2 = Thread(target=self.reader, args=(p.stderr, "stderr"))
        t2.start()
        p.wait()
        t1.join()
        t2.join()
        if progress is not None:
            progress("done.", "main")
        else:
            sys.stderr.write("done.\n")
        # Clean up - no longer needed
        os.unlink(distpath)

    def install_setuptools(self, context):
        """
        Install setuptools in the virtual environment.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        url = "https://bitbucket.org/pypa/setuptools/downloads/ez_setup.py"
        self.install_script(context, "setuptools", url)
        # clear up the setuptools archive which gets downloaded
        pred = lambda o: o.startswith("setuptools-") and o.endswith(".tar.gz")
        files = filter(pred, os.listdir(context.bin_path))
        for f in files:
            f = os.path.join(context.bin_path, f)
            os.unlink(f)

    def install_pip(self, context):
        """
        Install pip in the virtual environment.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        url = "https://bootstrap.pypa.io/get-pip.py"
        self.install_script(context, "pip", url)


def remove_virtual_env():
    remove_file_or_dir(FLAGS.virtual_env_path, True)


def create_virtual_env():
    builder = ExtendedEnvBuilder()
    builder.create(FLAGS.virtual_env_path)
    with open(os.path.join(FLAGS.virtual_env_path, ".gitignore"), "w") as f:
        f.writelines(["*"])
    log(f"Create virtual environment {FLAGS.virtual_env_path}")


def install_module_in_virtual_env():
    pip_in_virtual_env = os.path.join(FLAGS.virtual_env_path, "bin/python")
    runarguments = [pip_in_virtual_env, "-m", "pip", "install", os.path.join(FLAGS.cwd, "dist/vrpc-0.0.9-cp38-cp38-linux_x86_64.whl")]
    try:
        p = subprocess.Popen(runarguments, cwd=FLAGS.cwd)
        logging.info("Running pip")
        time.sleep(10)
        logging.info("Sending stop signal")
        p.send_signal(signal.SIGTERM)
        p.wait()
        fail_if(p.returncode != 0, f"pip failed {p.returncode}")
    except Exception:
        logging.error(traceback.format_exc())
        fail("pip failed")



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

    parser.add_argument("--enable-logging", action="store_true", required=False, help="Enable logging.")
    parser.add_argument(
        "--enable-stats",
        action="store_true",
        required=False,
        help="Enable statistics collection.",
    )

    FLAGS = parser.parse_args()
    FLAGS.module_name = "vrpc"
    FLAGS.cwd = get_cwd()
    FLAGS.virtual_env_path = os.path.join(FLAGS.cwd, "xx")
    FLAGS.dist_dir = os.path.join(get_cwd(), "dist")
    FLAGS.base_dir = os.path.join(get_cwd(), FLAGS.module_name)
    FLAGS.session_dir = os.path.join(get_cwd(), "session")
    FLAGS.persistent_dir = os.path.join(get_cwd(), "persistent")
    print(sys.executable)
    # Determine the versions from VERSION file.
    get_version()
    # reset_version()
    # bump_to_version()
    # remove_session_dir()
    # remove_persistent_dir()
    # generate_proto_code()
    # do_sort_import()
    # do_format_black()
    # do_format_yapf()
    # do_mypy_test()
    # create_virtual_env()
    install_module_in_virtual_env()


    # do_cythonize()
    # # run_module()
