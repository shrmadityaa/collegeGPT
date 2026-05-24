import pickle
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "capstone2.0"))

from utils.syllabus import build_semester_course_catalog


class SemesterCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chunks_path = PROJECT_ROOT / "capstone2.0" / "extracted" / "chunks.pkl"
        with chunks_path.open("rb") as handle:
            chunks = pickle.load(handle)
        cls.semester_courses, cls.course_lookup = build_semester_course_catalog(chunks)

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
                "ltp": "3-0-2",
                "credits": "4",
                "semester": "SEMESTER-III",
            },
        )


if __name__ == "__main__":
    unittest.main()
