"""Verifier must fail clearly when reports are missing or inconsistent."""

import json

import pytest

from dataflow.verify import verify


def test_missing_reports_fail(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify(tmp_path)


def test_invalid_audit_disposition_fails(tmp_path):
    (tmp_path / "quality_summary.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "run_summary.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "row_audit.csv").write_text(
        "source_file,source_line,key_sha256,row_sha256,disposition,reason_code\n"
        "sales.csv,2,,,unknown,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unknown audit disposition"):
        verify(tmp_path)
