"""The same pinned skill must hash identically after Windows and Linux checkouts."""

import hashlib
from pathlib import Path

from tooling.policy import tree_digest


def test_tree_digest_has_case_sensitive_portable_order(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_bytes(b"lower\n")
    (tmp_path / "A.txt").write_bytes(b"upper\n")
    expected = hashlib.sha256(b"A.txt\0upper\n\0b.txt\0lower\n\0").hexdigest()
    assert tree_digest(tmp_path) == expected
