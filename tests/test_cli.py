from __future__ import annotations

import json
from pathlib import Path

from arena.cli import main


def test_cli_list_bots(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["arena-cli", "--list-bots"])
    code = main()
    out = capsys.readouterr().out
    assert code == 0
    assert "random" in out
    assert "greedy" in out
    assert "minimax" in out
    assert "mcts" in out


def test_cli_list_presets(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["arena-cli", "--list-presets"])
    code = main()
    out = capsys.readouterr().out
    assert code == 0
    assert "baseline-6" in out


def test_cli_writes_markdown_and_json(monkeypatch, tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "leaderboard.md"
    json_path = tmp_path / "matches.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "arena-cli",
            "--bots",
            "random",
            "greedy",
            "--rounds",
            "1",
            "--games-per-pair",
            "2",
            "--seed",
            "9",
            "--markdown-out",
            str(md_path),
            "--json-out",
            str(json_path),
        ],
    )
    code = main()
    out = capsys.readouterr().out

    assert code == 0
    assert "Rank" in out
    assert md_path.exists()
    assert json_path.exists()

    md_text = md_path.read_text(encoding="utf-8")
    assert "Arena Leaderboard" in md_text
    assert "Head-to-Head" in md_text

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert "ratings" in payload
    assert "records" in payload
    assert len(payload["records"]) == 2


def test_cli_preset_allows_overrides(monkeypatch, tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "preset.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "arena-cli",
            "--preset",
            "baseline-6",
            "--bots",
            "random",
            "greedy",
            "--rounds",
            "1",
            "--games-per-pair",
            "1",
            "--markdown-out",
            str(md_path),
        ],
    )
    code = main()
    out = capsys.readouterr().out
    assert code == 0
    assert "Rank" in out
    assert md_path.exists()
