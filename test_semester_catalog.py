import pickle
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "capstone2.0"))

from utils.syllabus import (
    build_course_name_index,
    build_elective_catalog,
    build_semester_course_catalog,
    collect_ai_related_subjects,
    extract_focus_areas,
    filter_electives_for_query,
    filter_valid_subject_rows,
    format_semester_label,
    is_pcc_listing_row,
    match_query_to_courses,
)


class SemesterCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chunks_path = PROJECT_ROOT / "capstone2.0" / "extracted" / "chunks.pkl"
        with chunks_path.open("rb") as handle:
            chunks = pickle.load(handle)
        cls.chunks = chunks
        cls.semester_courses, cls.course_lookup = build_semester_course_catalog(chunks)
        cls.course_name_index = build_course_name_index(cls.course_lookup)
        cls.elective_catalog = build_elective_catalog(chunks)

    def test_semester_one_subjects_are_strict(self):
        semester_one = [
            (row["course_code"], row["course_name"])
            for row in self.semester_courses["SEMESTER-I"]
        ]
        self.assertEqual(
            semester_one,
            [
                ("UCB009", "Chemistry"),
                ("UES103", "Programming for Problem Solving"),
                ("UES013", "Electrical & Electronics Engineering"),
                ("UEN008", "Energy and Environment"),
                ("UMA022", "Calculus for Engineers"),
            ],
        )

    def test_operating_systems_resolves_to_semester_three(self):
        self.assertEqual(
            self.course_lookup["UCS303"],
            {
                "course_code": "UCS303",
                "course_name": "Operating System",
                "code_type": "PCC",
                "ltp": "3-0-2",
                "credits": "4",
                "semester": "SEMESTER-III",
            },
        )

    def test_machine_learning_course_name_query_maps_exactly(self):
        matches = match_query_to_courses(
            "What is the credit of Machine Learning?",
            self.course_lookup,
            self.course_name_index,
        )
        self.assertEqual(matches[0]["course_code"], "UML501")
        self.assertEqual(matches[0]["semester"], "SEMESTER-V")

    def test_computer_network_singular_query_maps_to_computer_networks(self):
        matches = match_query_to_courses(
            "Computer Network topics",
            self.course_lookup,
            self.course_name_index,
        )
        self.assertEqual(matches[0]["course_code"], "UCS414")

    def test_ai_related_elective_filter_returns_multiple_ai_electives(self):
        course_codes = {
            entry["course_code"]
            for entry in filter_electives_for_query("AI-related electives", self.elective_catalog)
        }
        self.assertTrue({"UCS551", "UCS664", "UCS748"}.issubset(course_codes))

    def test_pcc_rows_preserve_code_type(self):
        semester_five_pcc = {
            row["course_code"]
            for row in self.semester_courses["SEMESTER-V"]
            if row.get("code_type") == "PCC"
        }
        self.assertTrue({"UML501", "UCS553", "UCS503"}.issubset(semester_five_pcc))

    def test_semester_label_keeps_roman_numerals_uppercase(self):
        self.assertEqual(format_semester_label("SEMESTER-II"), "Semester II")
        self.assertEqual(format_semester_label("SEMESTER-VIII"), "Semester VIII")

    def test_pcc_listing_includes_foundational_semester_one_and_two_rows(self):
        semester_one_rows = [
            row["course_code"]
            for row in self.semester_courses["SEMESTER-I"]
            if is_pcc_listing_row("SEMESTER-I", row)
        ]
        semester_two_rows = [
            row["course_code"]
            for row in self.semester_courses["SEMESTER-II"]
            if is_pcc_listing_row("SEMESTER-II", row)
        ]
        self.assertEqual(
            semester_one_rows,
            ["UCB009", "UES103", "UES013", "UEN008", "UMA022"],
        )
        self.assertEqual(
            semester_two_rows,
            ["UPH013", "UES101", "UHU003", "UES102", "UMA023"],
        )

    def test_semester_six_cleanup_removes_corrupted_merged_row(self):
        semester_six_rows = filter_valid_subject_rows(self.semester_courses["SEMESTER-VI"])
        semester_six_codes = [row["course_code"] for row in semester_six_rows]
        self.assertEqual(semester_six_codes, ["UCS701", "UMA035", "UTA025"])

    def test_semester_seven_keeps_valid_capstone_project(self):
        semester_seven_rows = filter_valid_subject_rows(self.semester_courses["SEMESTER-VII"])
        semester_seven_codes = [row["course_code"] for row in semester_seven_rows]
        self.assertIn("UCS797", semester_seven_codes)

    def test_ai_curriculum_aggregation_returns_core_and_elective_matches(self):
        core_subjects, elective_subjects = collect_ai_related_subjects(
            self.semester_courses,
            self.elective_catalog,
        )
        core_codes = {row["course_code"] for row in core_subjects}
        elective_codes = {row["course_code"] for row in elective_subjects}
        self.assertTrue({"UCS321", "UML501", "UCS714"}.issubset(core_codes))
        self.assertTrue({"UCS551", "UCS664", "UCS748"}.issubset(elective_codes))

    def test_focus_area_extraction_returns_multiple_domains(self):
        focus_names = {item["name"] for item in extract_focus_areas(self.chunks)}
        self.assertTrue(
            {
                "Information and Cyber Security",
                "Conversational AI (NVIDIA Collaboration)",
                "Intelligent Transport Systems",
            }.issubset(focus_names)
        )


if __name__ == "__main__":
    unittest.main()
