from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import SourceConfig


CANDIDATES = Path(__file__).parents[1] / "sandbox" / "candidates"


@pytest.mark.parametrize("name", ["baseline.json", "good.json"])
def test_valid_sandbox_candidates_pass_full_schema(name: str) -> None:
    config = SourceConfig.model_validate_json((CANDIDATES / name).read_bytes())
    assert config.service_id == "photo-api"


def test_bad_sandbox_candidate_fails_before_service_start() -> None:
    with pytest.raises(ValidationError):
        SourceConfig.model_validate_json((CANDIDATES / "bad.json").read_bytes())


def test_sandbox_candidates_contain_no_secret_fields() -> None:
    for path in CANDIDATES.glob("*.json"):
        text = path.read_text(encoding="utf-8").casefold()
        assert "password" not in text
        assert "secret" not in text
        assert "token" not in text
