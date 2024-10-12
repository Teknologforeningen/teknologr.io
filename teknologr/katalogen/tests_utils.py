from django.test import TestCase
from datetime import date
from .utils import *

class DurationTests(TestCase):
    def setUp(self):
        self.d1 = date(1998, 1, 1)
        self.d2 = date(1998, 1, 30)
        self.d3 = date(1998, 12, 31)
        self.d4 = date(2000, 12, 31)
        self.d5 = date(2001, 7, 7)
        self.d6 = date(2002, 12, 31)

    def test_same_date(self):
        self.assertEqual('1 januari 1998', Duration(self.d1, self.d1).to_string())

    def test_same_month(self):
        self.assertEqual('1–30 januari 1998', Duration(self.d1, self.d2).to_string())

    def test_same_year(self):
        self.assertEqual('30 januari – 31 december 1998', Duration(self.d2, self.d3).to_string())

    def test_whole_years(self):
        self.assertEqual('1998', Duration(self.d1, self.d3).to_string())
        self.assertEqual('1998–2000', Duration(self.d1, self.d4).to_string())

    def test_no_simplification(self):
        self.assertEqual('1 januari 1998 – 7 juli 2001', Duration(self.d1, self.d5).to_string())
        self.assertEqual('7 juli 2001 – 31 december 2002', Duration(self.d5, self.d6).to_string())

class MultiDurationTests(TestCase):
    def test_not_overlapping(self):
        dur1 = Duration(date(2000, 1, 1), date(2000, 1, 30))
        dur2 = Duration(date(2000, 2, 1), date(2000, 2, 28))
        self.assertEqual([dur1, dur2], MultiDuration([dur1, dur2]))
        self.assertEqual([dur1, dur2], MultiDuration([dur2, dur1]))

    def test_sequetial(self):
        dur1 = Duration(date(2000, 1, 1), date(2000, 1, 31))
        dur2 = Duration(date(2000, 2, 1), date(2000, 2, 28))
        dur3 = Duration(date(2000, 1, 1), date(2000, 2, 28))
        self.assertEqual([dur3], MultiDuration([dur1, dur2]))
        self.assertEqual([dur3], MultiDuration([dur2, dur1]))

    def test_overlapping(self):
        dur1 = Duration(date(2000, 1, 1), date(2000, 2, 28))
        dur2 = Duration(date(2000, 2, 1), date(2000, 3, 31))
        dur3 = Duration(date(2000, 1, 1), date(2000, 3, 31))
        self.assertEqual([dur3], MultiDuration([dur1, dur2]))
        self.assertEqual([dur3], MultiDuration([dur2, dur1]))

    def test_containing(self):
        dur1 = Duration(date(2000, 1, 1), date(2000, 3, 31))
        dur2 = Duration(date(2000, 2, 1), date(2000, 2, 28))
        dur3 = Duration(date(2000, 1, 1), date(2000, 3, 31))
        self.assertEqual([dur3], MultiDuration([dur1, dur2]))
        self.assertEqual([dur3], MultiDuration([dur2, dur1]))

    def test_empty(self):
        self.assertEqual([], MultiDuration([]))

    def test_combine_per_key(self):
        result = MultiDuration.combine_per_key([
            (9, Duration(date(2000, 1, 1), date(2000, 12, 31))),
            (1, Duration(date(2000, 1, 1), date(2000, 1, 31))),
            (1, Duration(date(2000, 3, 1), date(2000, 3, 31))),
            (1, Duration(date(2000, 5, 1), date(2000, 5, 31))),
            (1, Duration(date(2000, 7, 1), date(2000, 7, 31))),
            (1, Duration(date(2000, 9, 1), date(2000, 9, 30))),
            (8, Duration(date(2000, 1, 1), date(2000, 12, 31))),

            (1, Duration(date(2000, 1, 5), date(2000, 1, 6))),
            (1, Duration(date(2000, 3, 7), date(2000, 7, 7))),
        ])
        result = [(r[0], r[1].to_string()) for r in result]
        self.assertEqual([
            (9, '2000'),
            (1, '1–31 januari 2000, 1 mars – 31 juli 2000, 1–30 september 2000'),
            (8, '2000'),
        ], result)
