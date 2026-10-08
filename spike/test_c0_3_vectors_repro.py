"""C0.3: sinh lại bộ vector phải ra đúng từng byte bản đã commit."""

from __future__ import annotations

from pathlib import Path

import gen_fm1_vectors as G


def test_sinh_lai_ra_dung_tung_byte(tmp_path: Path):
    G.write(tmp_path)
    committed = sorted(G.OUT_DEFAULT.glob("*.json"))
    fresh = sorted(tmp_path.glob("*.json"))
    assert [p.name for p in committed] == [p.name for p in fresh]
    for a, b in zip(committed, fresh):
        assert a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes(), a.name
