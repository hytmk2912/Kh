import pathlib
import re

from kh.ind.indicators.registry import CARDS

SPEC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "ind" / "spec.md"


def appendix_names() -> list[str]:
    s = SPEC.read_text()
    names = []
    for line in s[s.index("## Phụ lục A"):].splitlines():
        m = re.match(r"- \*\*A\d\. [^:]*:\*\*(.*)", line)
        if m:
            body = re.sub(r"\([^)]*\)", "", m.group(1)).replace("—", ",")
            names += [x.strip() for x in re.split(r"[,;]", body) if x.strip()]
    return names


def test_registry_covers_appendix_exactly():
    names = appendix_names()
    assert len(names) == len(set(names)) == 101
    assert [c.name for c in CARDS] == names, "registry phải có đúng và đủ tên ở Phụ lục A, cùng thứ tự"


def test_cards_complete():
    for c in CARDS:
        assert c.kind in ("D", "F")
        if c.not_implementable:
            continue
        assert c.formula and c.rule and isinstance(c.params, dict) and c.warmup >= 0
