#! env python3
import importlib
import math
import unittest
from datetime import datetime, timedelta

jiraManager = importlib.import_module("jiraManager")
calcTimeBetween = jiraManager.calcTimeBetween

today = datetime.strptime("21/08/2019 16:00:00", "%d/%m/%Y %H:%M:%S")


def minutesBetween(time1, time2):
    return math.floor((calcTimeBetween(time1, time2)).total_seconds() / 60)


class TestCalcTimeBetween(unittest.TestCase):
    def test_before_noon(self):
        start = today.replace(hour=9, minute=0)
        end = today.replace(hour=12, minute=0)

        self.assertEqual(minutesBetween(start, end), 3 * 60)

    def test_after_noon(self):
        start = today.replace(hour=13, minute=30)
        end = today.replace(hour=14, minute=30)

        self.assertEqual(minutesBetween(start, end), 60)

    def test_including_noon(self):
        start = today.replace(hour=12, minute=0)
        end = today.replace(hour=14, minute=0)

        self.assertEqual(minutesBetween(start, end), 80)

    def test_including_night(self):
        start = today.replace(hour=16, minute=0)
        end = today.replace(hour=9, minute=0) + timedelta(days=1)

        self.assertEqual(minutesBetween(start, end), 88)

    def test_including_noon_and_night(self):
        start = today.replace(hour=11, minute=0)
        end = today.replace(hour=9, minute=0) + timedelta(days=1)

        self.assertEqual(minutesBetween(start, end), 348)

    def test_including_weekend(self):
        friday = datetime.strptime("23/08/2019 16:00:00", "%d/%m/%Y %H:%M:%S")
        monday = datetime.strptime("26/08/2019 9:00:00", "%d/%m/%Y %H:%M:%S")

        self.assertEqual(minutesBetween(friday, monday), 88)

    def test_two_days_straight(self):
        start = datetime.strptime("19/08/2019 9:00:00", "%d/%m/%Y %H:%M:%S")
        stop = datetime.strptime("21/08/2019 17:15:00", "%d/%m/%Y %H:%M:%S")

        self.assertEqual(minutesBetween(start, stop), 1391)


if __name__ == "__main__":
    unittest.main()
