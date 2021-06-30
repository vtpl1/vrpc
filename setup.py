#!/usr/bin/env python3
import codecs
import glob
import os
import pathlib
from subprocess import check_call

from setuptools.command.develop import develop

# the below order is important from setuptools import find_packages, setup then from Cython.Build import cythonize
from setuptools import find_packages, setup  # isort:skip

from Cython.Build import cythonize  # isort:skip


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def read_lines(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.readlines()


def get_version():
    return read("vrpc/VERSION")


def get_install_requires():
    # return [
    #     "ruamel.yaml",
    #     "numpy",
    #     "zope.event",
    #     "pynng",
    #     "marshmallow",
    #     "marshmallow_dataclass",
    #     "mysql-connector-python",
    #     "opencv-python",
    #     "torch",
    #     "torchvision",
    #     "torchaudio",
    #     "dataclasses",
    #     "vtpl_analytics_api@git+https://github.com/vtpl1/videonetics_api.git",
    #     "singleton_decorator@git+https://github.com/vtpl1/singleton_decorator.git",
    #     "check_cuda@git+https://github.com/vtpl1/check_cuda.git",
    # ]
    # return []
    return [
        line.strip() for line in read_lines("requirements.prod.txt")
        if line.strip()
    ]


def generate_proto_code():
    proto_interface_dir = "./vrpc/data_models/interfaces"
    generated_src_dir = "./vrpc/data_models/generated/"
    out_folder = "vrpc/data_models"
    if not os.path.exists(generated_src_dir):
        os.mkdir(generated_src_dir)
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    proto_path = "generated=" + proto_interface_dir
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    check_call(["protoc"] + protos +
               ["--python_out", out_folder, "--proto_path", proto_path])


class CustomDevelopCommand(develop):
    """Wrapper for custom commands to run before package installation."""

    uninstall = False

    def run(self):
        develop.run(self)

    def install_for_development(self):
        develop.install_for_development(self)
        generate_proto_code()


def get_python_files():
    l = []
    for z in [
            y + os.path.sep + "*.py" for y in [
                x.replace(".", os.path.sep)
                for x in find_packages(exclude=["*.tests", "test", "session"])
            ]
    ]:
        l.extend(glob.glob(z))
    return [a for a in l if not a.endswith("__init__.py")]


setup(
    # dependency_links=[
    #     'git+https://github.com/vtpl1/singleton_decorator.git@master#egg=singleton-decorator'
    # ],
    install_requires=get_install_requires(),
    name="vrpc",
    version=get_version(),
    description="Videonetics deeperlook Framework",
    author="Monotosh Das",
    author_email="monotosh.das@videonetics.com",
    url="http://pypi.videonetics.com",
    keywords="video analytics framework vas",
    classifiers=["License :: OSI Approved :: MIT License"],
    include_package_data=True,
    cmdclass={
        "develop": CustomDevelopCommand,  # used for pip install -e ./
    },
    packages=find_packages(
        exclude=["*.tests", "test", "tests", "session", "videos"]),
    # package_dir={'negar': 'negar'},
    package_data={"": ["*.yaml", "VERSION", "*.jpg", "*.so", "*.mp4"]},
    entry_points={
        "console_scripts": [
            "vrpc = vrpc.main:main",
        ],
    },
    # ext_modules=cythonize([
    #     x + os.path.sep + '*.py' for x in [
    #         x.replace('.', os.path.sep) for x in find_packages(exclude=["*.tests", "test", "session"])
    #     ]
    # ]),
    ext_modules=cythonize(get_python_files(), language_level="3"),
    zip_safe=False,
)
