# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

# NO_ruff: noqa: T201, T203 `print` found

from __future__ import annotations

import datetime
import importlib.metadata
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import toml
from typing_extensions import Self

from .util import singleton

# def get_project_info():
#     # Get the project name and version from the installed package metadata
#     try:
#         distribution = pkg_resources.get_distribution("your_project_name")
#         project_name = distribution.project_name
#         project_version = distribution.version
#     except pkg_resources.DistributionNotFound:
#         project_name = "Unknown"
#         project_version = "Unknown"

#     # Get the project folder
#     project_folder = os.path.dirname(os.path.abspath(__file__))

#     return {
#         "project_name": project_name,
#         "project_version": project_version,
#         "project_folder": project_folder,
#     }


# def get_git_info():
#     pass


@dataclass
class HWInfo:
    cpu: str
    ram: str
    gpu: str

    def slug(self) -> str:
        return f"{self.cpu}_{self.ram}_{self.gpu}"

    def to_dict(self) -> dict[str, Any]:
        return {"cpu": self.cpu, "ram": self.ram, "gpu": self.gpu}

    @classmethod
    def create(cls) -> Self:
        return cls(
            cpu="Intel Core i7-10700K", ram="32 GB", gpu="NVIDIA GeForce RTX 2070"
        )


@dataclass
class ProjectInfo:
    name: str
    version: str
    root_folder: Path
    pyproject_toml: dict | None = None

    def slug(self) -> str:
        return f"v{self.version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "root_folder": str(self.root_folder),
        }

    @classmethod
    def create(cls, *, project_name: str, project_root: Path) -> Self:
        if not project_root.is_dir():
            raise FileNotFoundError(f"Folder not found: {project_root}")
        if not (project_root / "setup.py").is_file():
            raise FileNotFoundError(f"setup.py not found in: {project_root}")
        project_version = importlib.metadata.version(project_name)
        meta = importlib.metadata.metadata(project_name)
        project_name = meta["Name"]
        # project_name = importlib.metadata.distribution("nutree").project_name
        project_info = cls(
            root_folder=project_root,
            name=project_name,
            version=project_version,
        )
        # read pyproject.toml
        try:
            with open(project_root / "pyproject.toml") as f:
                project_info.pyproject_toml = toml.load(f)
        except FileNotFoundError:
            pass

        return project_info


@dataclass
class OSInfo:
    name: str
    version: str

    def slug(self) -> str:
        return f"{self.name}_{self.version}"

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "version": self.version}

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "implementation": self.implementation,
            "compiler": self.compiler,
            "build": self.build,
        }

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

    def __init__(self, *, project_name: str, project_root: Path | str) -> None:
        root_path = Path(project_root)
        self.hostname = socket.gethostname()
        # self.comment = comment
        self.date = datetime.datetime.now()
        self.python: PythonInfo = PythonInfo.create()
        self.os: OSInfo = OSInfo.create()
        self.hw: HWInfo = HWInfo.create()
        self.project: ProjectInfo = ProjectInfo.create(
            project_name=project_name, project_root=root_path
        )

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.hostname}>"

    def slug(self) -> str:
        return "$".join(
            [
                self.hostname,
                self.date.strftime("%Y%m%d"),
                self.os.slug(),
                self.hw.slug(),
                self.project.slug(),
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hostname": self.hostname,
            "date": self.date.isoformat(),
            "python": self.python.to_dict(),
            "os": self.os.to_dict(),
            "hw": self.hw.to_dict(),
            "project": self.project.to_dict(),
        }
