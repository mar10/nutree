# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

# NO_ruff: noqa: T201, T203 `print` found
from __future__ import annotations

import datetime
import os
import socket
from dataclasses import dataclass

import pkg_resources
from typing_extensions import Self

from .util import singleton


def get_project_info():
    # Get the project name and version from the installed package metadata
    try:
        distribution = pkg_resources.get_distribution("your_project_name")
        project_name = distribution.project_name
        project_version = distribution.version
    except pkg_resources.DistributionNotFound:
        project_name = "Unknown"
        project_version = "Unknown"

    # Get the project folder
    project_folder = os.path.dirname(os.path.abspath(__file__))

    return {
        "project_name": project_name,
        "project_version": project_version,
        "project_folder": project_folder,
    }


# def get_git_info():
#     pass


@dataclass
class HWInfo:
    cpu: str
    ram: str
    gpu: str

    def slug(self) -> str:
        return f"{self.cpu}_{self.ram}_{self.gpu}"

    @classmethod
    def create(cls) -> Self:
        return cls(
            cpu="Intel Core i7-10700K", ram="32 GB", gpu="NVIDIA GeForce RTX 2070"
        )


@dataclass
class ProjectInfo:
    name: str
    version: str
    folder: str

    def slug(self) -> str:
        return f"v{self.version}"

    @classmethod
    def create(cls) -> Self:
        return cls(name="your_project_name", version="0.1.0", folder="path/to/project")


@dataclass
class OSInfo:
    name: str
    version: str

    def slug(self) -> str:
        return f"{self.name}_{self.version}"

    @property
    def is_windows(self) -> bool:
        return self.name == "Windows"

    @classmethod
    def create(cls) -> Self:
        return cls(name="Windows", version="10.0.19042")


@dataclass
class PythonInfo:
    version: str
    implementation: str
    compiler: str
    build: str

    def slug(self) -> str:
        return f"{self.version}_{self.implementation}_{self.compiler}"

    @classmethod
    def create(cls) -> PythonInfo:
        return cls(
            version="3.9.7",
            implementation="CPython",
            compiler="MSC v.1916 64 bit (AMD64)",
            build="Sep 16 2021 15:21:35",
        )


@singleton
class BaseContextInfo:
    """
    Runtime context information about the client system (constant).
    """

    def __init__(self) -> None:
        self.hostname = socket.gethostname()
        # self.comment = comment
        self.date = datetime.datetime.now()
        self.python: PythonInfo = PythonInfo.create()
        self.os: OSInfo = OSInfo.create()
        self.hw: HWInfo = HWInfo.create()
        self.project: ProjectInfo = ProjectInfo.create()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.hostname}>"

    # @classmethod
    # def create(cls) -> Self:
    #     """
    #     docstring
    #     """
    #     self = cls()
    #     return self
