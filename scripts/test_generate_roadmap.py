"""N-BIP-02 AC-3: public フィルタのユニットテスト。"""

import tempfile
import unittest
from pathlib import Path

from generate_roadmap import load_tickets, parse_frontmatter


class TestPublicFilter(unittest.TestCase):
    def test_parse_frontmatter_public_true(self):
        content = """---
id: "TEST-01"
status: "goal"
public: true
product: "NINJINE"
---
# Title
"""
        fm, _ = parse_frontmatter(content)
        self.assertTrue(fm.get("public") is True)

    def test_load_tickets_skips_private_and_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "public.md").write_text(
                """---
id: "PUB-01"
status: "goal"
public: true
product: "NINJINE"
---
# Public ticket
""",
                encoding="utf-8",
            )
            (d / "private.md").write_text(
                """---
id: "PRV-01"
status: "goal"
public: false
product: "NINJINE"
---
# Private
""",
                encoding="utf-8",
            )
            (d / "legacy.md").write_text("# No frontmatter\n", encoding="utf-8")

            tickets = load_tickets(d)
            ids = {t["id"] for t in tickets}
            self.assertEqual(ids, {"PUB-01"})


if __name__ == "__main__":
    unittest.main()
