from __future__ import annotations

from importlib.resources import files


def test_package_declares_inline_types() -> None:
    assert files("assignment_selection").joinpath("py.typed").is_file()
