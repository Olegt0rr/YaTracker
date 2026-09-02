"""Run mypy over the static typing cases in ``tests/typing_cases``.

The cases use ``assert_type`` to pin overload resolution, which pytest
alone cannot observe: ``@overload`` stubs have no runtime effect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

mypy_api = pytest.importorskip("mypy.api")

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "tests" / "typing_cases"


@pytest.mark.parametrize("case", sorted(CASES.glob("*.py")), ids=lambda p: p.stem)
def test_typing_case(case: Path, tmp_path: Path) -> None:
    stdout, stderr, status = mypy_api.run(
        [
            "--config-file",
            str(ROOT / "pyproject.toml"),
            "--cache-dir",
            str(tmp_path / "mypy_cache"),
            # Without this, mypy names the file tests.typing_cases.* and the
            # ignore_errors override for tests.* in pyproject.toml masks failures.
            "--no-namespace-packages",
            "--no-error-summary",
            str(case),
        ],
    )
    assert status == 0, stdout + stderr
