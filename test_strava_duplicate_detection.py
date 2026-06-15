import datetime
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent / "run_page"))

from generator import Generator  # noqa: E402
from generator.db import Activity  # noqa: E402


UTC = datetime.timezone.utc


def _file_run_id(start_date):
    return int(start_date.timestamp() * 1000)


class StravaDuplicateDetectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.generator = Generator(str(Path(self.tmp.name) / "data.db"))

    def tearDown(self):
        bind = self.generator.session.get_bind()
        self.generator.session.close()
        bind.dispose()

    def add_activity(self, run_id, start_date, distance):
        self.generator.session.add(
            Activity(
                run_id=run_id,
                name="",
                distance=distance,
                type="Run",
                start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"),
                start_date_local=start_date.strftime("%Y-%m-%d %H:%M:%S"),
                average_speed=2.5,
            )
        )
        self.generator.session.commit()

    def test_matches_file_import_when_time_and_distance_are_close(self):
        start_date = datetime.datetime(2026, 6, 12, 23, 58, 26, tzinfo=UTC)
        local_run_id = _file_run_id(start_date)
        self.add_activity(local_run_id, start_date, 10018.92)

        strava_activity = SimpleNamespace(
            id=12345678901,
            start_date=start_date + datetime.timedelta(seconds=90),
            distance=10100.0,
        )

        duplicate = self.generator.find_matching_file_import_activity(strava_activity)

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.run_id, local_run_id)

    def test_ignores_non_file_imported_activity_with_same_time_and_distance(self):
        start_date = datetime.datetime(2026, 6, 12, 23, 58, 26, tzinfo=UTC)
        self.add_activity(12345678901, start_date, 10018.92)

        strava_activity = SimpleNamespace(
            id=12345678902,
            start_date=start_date,
            distance=10018.92,
        )

        duplicate = self.generator.find_matching_file_import_activity(strava_activity)

        self.assertIsNone(duplicate)

    def test_does_not_match_when_time_or_distance_is_outside_window(self):
        start_date = datetime.datetime(2026, 6, 12, 23, 58, 26, tzinfo=UTC)
        self.add_activity(_file_run_id(start_date), start_date, 10018.92)

        too_late = SimpleNamespace(
            id=12345678901,
            start_date=start_date + datetime.timedelta(minutes=6),
            distance=10018.92,
        )
        too_far = SimpleNamespace(
            id=12345678902,
            start_date=start_date,
            distance=9500.0,
        )

        self.assertIsNone(self.generator.find_matching_file_import_activity(too_late))
        self.assertIsNone(self.generator.find_matching_file_import_activity(too_far))


if __name__ == "__main__":
    unittest.main()
