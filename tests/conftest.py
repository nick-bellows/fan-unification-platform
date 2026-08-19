from pathlib import Path

import pytest

from fanuni.generator.model import GenConfig
from fanuni.generator.run import generate


@pytest.fixture(scope="session")
def small_dataset(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    """One shared small generation for every test that reads source files."""
    out = tmp_path_factory.mktemp("dataset")
    manifest = generate(GenConfig(seed=7, fans=400, out_dir=str(out)))
    return out, manifest
