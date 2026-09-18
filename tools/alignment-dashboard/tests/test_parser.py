"""Parser tests against real issue bodies.

The fixtures are copied verbatim from the issues named in each test. Between
them they cover every shape found in the repo: the four row formats, the
context-line platform, bare #N inheriting a repo, code permalinks, and the
template boilerplate that must never be read as tracking data.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import cell_state
from parser import (count_checkbox_rows, extract_refs, load_config,
                    normalize_platform, parse_issue)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CFG = load_config()


def body(number):
    with open(os.path.join(FIXTURES, f"issue-{number}.md")) as fh:
        return fh.read()


def rows_for(number):
    return parse_issue(number, body(number), CFG)[0]


class TestSections(unittest.TestCase):
    def test_boilerplate_is_excluded(self):
        """#99 carries a Code of Conduct block; only Sub-tasks is tracking."""
        rows = rows_for(99)
        self.assertTrue(rows, "expected tracking rows in #99")
        for row in rows:
            self.assertNotIn(row["heading"].lower(), ("code of conduct", "checklist"))

    def test_tracking_rows_are_a_subset_of_all_checkboxes(self):
        for number in (115, 119, 121, 145, 146, 99):
            with self.subTest(issue=number):
                self.assertLessEqual(len(rows_for(number)),
                                     count_checkbox_rows(body(number)))

    def test_star_bullets_are_rows(self):
        """#15 uses `* [X]` rather than `- [x]`."""
        self.assertTrue(rows_for(15))


class TestPlatformAttribution(unittest.TestCase):
    def test_label_before_separator(self):
        rows = rows_for(115)
        platforms = {r["platform"] for r in rows if r["platform"]}
        self.assertIn("android", platforms)
        self.assertIn("apple", platforms)
        self.assertIn("web", platforms)

    def test_aspects_split_two_android_rows(self):
        """#115 tracks Android twice: display, and the editing move."""
        android = [r for r in rows_for(115) if r["platform"] == "android"]
        self.assertGreaterEqual(len(android), 2)
        self.assertTrue(any(r["aspect"] for r in android))

    def test_baseui_and_mui_alias_to_real_repos(self):
        self.assertEqual(normalize_platform("BaseUI", CFG)[0], "firmware")
        self.assertEqual(normalize_platform("MUI", CFG)[0], "mui")
        self.assertEqual(normalize_platform("Apple", CFG)[0], "apple")

    def test_ref_leading_rows_take_platform_from_repo(self):
        """#121 rows start with the link and carry no label."""
        rows = rows_for(121)
        by_ref = [r for r in rows if r["how"] == "ref"]
        self.assertTrue(by_ref, "expected rows attributed by their linked repo")

    def test_context_line_sets_platform(self):
        """#145 puts the platform on a bare `Apple:` line above the rows."""
        rows = rows_for(145)
        self.assertTrue(any(r["how"] == "context" for r in rows),
                        "expected at least one row attributed by context line")

    def test_meta_rows_are_not_platforms(self):
        """`Create Android alignment issue` is about filing, not a platform."""
        rows = rows_for(99)
        meta = [r for r in rows if r["how"] == "meta"]
        self.assertTrue(meta)
        for row in meta:
            self.assertIsNone(row["platform"])


    def test_alias_containing_commas_is_not_split(self):
        """'Apple (iOS, iPadOS, macOS)' must not become 'Apple (iOS'."""
        rows, _ = parse_issue(1, '## Platform Tracking'+chr(10)+chr(10)+
                                 '- [x] Apple (iOS, iPadOS, macOS), Meshtastic-Apple#1996'+chr(10),
                              CFG)
        self.assertEqual(rows[0]['platform'], 'apple')
        self.assertIsNone(rows[0]['aspect'])

    def test_aspect_survives_the_alias_match(self):
        rows, _ = parse_issue(1, '## Platform Tracking'+chr(10)+chr(10)+
                                 '- [x] Android display, Meshtastic-Android#5987'+chr(10),
                              CFG)
        self.assertEqual(rows[0]['platform'], 'android')
        self.assertEqual(rows[0]['aspect'], 'display')


class TestReferences(unittest.TestCase):
    def test_bare_number_inherits_repo_from_the_row(self):
        """In #115, `#4163` follows Meshtastic-Android#5987 and means Android."""
        refs = extract_refs(
            "Android display, Meshtastic-Android#5987, shipped in #4163 and #4577",
            CFG["repo_shorthand"])
        self.assertEqual(refs[0]["repo"], "meshtastic/Meshtastic-Android")
        inherited = [r for r in refs if r["inherited"]]
        self.assertTrue(inherited)
        for ref in inherited:
            self.assertEqual(ref["repo"], "meshtastic/Meshtastic-Android")

    def test_shorthand_repo_names_map_to_real_repos(self):
        refs = extract_refs("Apple#2362 and Android#6932", CFG["repo_shorthand"])
        self.assertEqual({r["repo"] for r in refs},
                         {"meshtastic/Meshtastic-Apple",
                          "meshtastic/Meshtastic-Android"})

    def test_pull_and_issue_urls_are_distinguished(self):
        refs = extract_refs(
            "[#1](https://github.com/meshtastic/web/pull/1) and "
            "[#2](https://github.com/meshtastic/web/issues/2)",
            CFG["repo_shorthand"])
        self.assertEqual([r["kind"] for r in refs], ["PR", "ISSUE"])

    def test_code_permalinks_are_not_issue_numbers(self):
        refs = extract_refs(
            "see https://github.com/meshtastic/firmware/blob/master/src/x.cpp#L33",
            CFG["repo_shorthand"])
        self.assertEqual(refs, [])

    def test_inline_code_is_not_a_reference(self):
        self.assertEqual(extract_refs("the field `#1234` is internal",
                                      CFG["repo_shorthand"]), [])

    def test_markdown_link_yields_one_reference_not_two(self):
        refs = extract_refs(
            "[device-ui#332](https://github.com/meshtastic/device-ui/issues/332)",
            CFG["repo_shorthand"])
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["repo"], "meshtastic/device-ui")


    def test_bare_number_falls_back_to_the_row_platform(self):
        """#124: `the merged #2033 notice` on an Apple row means Apple#2033."""
        rows, _ = parse_issue(124, "## Tracking\n\n- [ ] Meshtastic Apple \u2014 "
                                   "replace the triangle in the merged #2033 notice\n",
                              CFG)
        self.assertEqual(rows[0]["platform"], "apple")
        self.assertEqual(rows[0]["refs"][0]["repo"], "meshtastic/Meshtastic-Apple")


class TestProvenance(unittest.TestCase):
    def test_every_row_keeps_its_text_and_line(self):
        for row in rows_for(115):
            self.assertTrue(row["text"])
            self.assertGreater(row["line"], 0)

    def test_unmapped_rows_are_emitted_not_dropped(self):
        """#120's `In-app event OTA` is a blocker, not a platform, and stays."""
        rows, _ = parse_issue(1, "## Platform Tracking\n\n"
                                 "- [ ] In-app event OTA, blocked on design#133\n",
                              CFG)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["platform"])
        self.assertTrue(rows[0]["blocked"])

    def test_out_of_scope_rows_are_detected(self):
        """design#157: firmware has nothing to do, so the row is a decision."""
        rows, _ = parse_issue(157, "## Platform Tracking\n\n"
                                   "- [ ] Firmware: out of scope, the defect is "
                                   "in how clients store a conversation\n", CFG)
        self.assertEqual(rows[0]["platform"], "firmware")
        self.assertTrue(rows[0]["outOfScope"])
        self.assertFalse(rows[0]["notFiled"])

    def test_not_yet_filed_is_not_out_of_scope(self):
        """"Not filed" means the work is owed; the two must not be confused."""
        rows, _ = parse_issue(157, "## Platform Tracking\n\n"
                                   "- [ ] Web: not yet filed, pending confirmation\n",
                              CFG)
        self.assertTrue(rows[0]["notFiled"])
        self.assertFalse(rows[0]["outOfScope"])


    def test_not_filed_phrases_are_detected(self):
        rows, _ = parse_issue(1, "## Platform Tracking\n\n"
                                 "- [ ] Web, no tracker opened\n", CFG)
        self.assertTrue(rows[0]["notFiled"])


class TestCellState(unittest.TestCase):
    """A cell can hold more than one row for the same platform."""

    @staticmethod
    def row(checked=False, oos=False, notfiled=False, blocked=False):
        return {"checked": checked, "outOfScope": oos, "notFiled": notfiled,
                "blocked": blocked, "text": ""}

    def test_every_row_out_of_scope_makes_the_cell_out_of_scope(self):
        state, _ = cell_state({"evidence": []}, [self.row(oos=True)])
        self.assertEqual(state, "not_applicable")

    def test_one_out_of_scope_row_does_not_excuse_the_platform(self):
        """The applicable row still owes work, so the cell is not excused."""
        state, _ = cell_state({"evidence": []},
                              [self.row(oos=True), self.row()])
        self.assertEqual(state, "not_filed")

    def test_out_of_scope_row_does_not_make_the_rest_look_claimed(self):
        """An unticked out-of-scope row must not drag all_checked down."""
        state, unverified = cell_state({"evidence": []},
                                       [self.row(oos=True), self.row(checked=True)])
        self.assertEqual(state, "claimed")
        self.assertTrue(unverified)

    def test_out_of_scope_row_does_not_import_its_not_filed_phrasing(self):
        state, _ = cell_state({"evidence": []},
                              [self.row(oos=True, notfiled=True), self.row(checked=True)])
        self.assertEqual(state, "claimed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
