from datetime import timedelta
from collections import defaultdict
from operator import attrgetter
from functools import total_ordering
from django.utils.formats import date_format

@total_ordering
class Duration:
    def __init__(self, begin_date, end_date):
        self.begin_date = begin_date
        self.end_date = end_date

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        return (self.end_date, self.begin_date) == (other.end_date, other.begin_date)

    def __lt__(self, other):
        return (self.end_date, self.begin_date) < (other.end_date, other.begin_date)

    def to_string(self):
        '''
        Turn the date interval into a string, where the dates are simplified as much as possible. These rules are as follows:
        - Same day:   A.B.YYYY – A.B.YYYY   -> 'A BB YYYY'
        - Same month: A.B.YYYY – C.B.YYYY   -> 'A–C BB YYYY'
        - Same year:  A.B.YYYY – C.D.YYYY   -> 'A BB – C DD YYYY'
        - Whole year: 1.1.YYYY – 31.12.YYYY -> 'YYYY'
        - Many years: 1.1.YYYY – 31.12.ZZZZ -> 'YYYY–ZZZZ'
        '''
        begin = self.begin_date
        end = self.end_date

        if begin.month == 1 and begin.day == 1 and end.month == 12 and end.day == 31:
            return f'{begin.year}' if begin.year == end.year else f'{begin.year}–{end.year}'

        b = date_format(begin)
        e = date_format(end)
        if begin.year != end.year:
            return f'{b} – {e}'
        if begin.month != end.month:
            i = b.rfind(' ')
            return f'{b[:i]} – {e}'
        if begin.day != end.day:
            return f'{begin.day}–{e}'
        return b

    def to_sort_string(self):
        return f'{self.end_date.isoformat()}{self.begin_date.isoformat()}'

@total_ordering
class MultiDuration:
    def __init__(self, durations):
        self.durations = MultiDuration.simplify(durations)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        other_durations = other.durations if isinstance(other, MultiDuration) else other
        if len(self.durations) != len(other_durations):
            return False
        for i in range(len(self.durations)):
            if self.durations[i] != other_durations[i]:
                return False
        return True

    def __lt__(self, other):
        n = min(len(self.durations), len(other.durations))
        for i in range(n):
            if self.durations[i] == other.durations[i]:
                continue
            return self.durations < other.durations
        return len(self.durations) < len(other.durations)

    def to_string(self):
        return ', '.join([str(d) for d in self.durations])

    def to_sort_string(self):
        return ','.join([d.to_sort_string() for d in self.durations])

    @classmethod
    def simplify(cls, durations):
        '''
        Overlapping durations will be simplified into a single duration.
        '''
        if not len(durations):
            return []

        durations.sort(key=attrgetter('begin_date'))

        simplified = [durations[0]]
        for next in durations[1:]:
            last = simplified[-1]
            if next.begin_date > last.end_date + timedelta(days=1):
                simplified.append(next)
            elif next.end_date > last.end_date:
                last.end_date = next.end_date

        return simplified

    @classmethod
    def combine_per_key(cls, items):
        '''
        The parameter is a list of (key, Duration) pairs. All durations with the same key will be combined into one MultiDuration.

        Returns a list of (key, MultiDuration) pairs.
        '''
        d = defaultdict(list)
        for key, duration in items:
            d[key].append(duration)
        return list((key, MultiDuration(durations)) for key, durations in d.items())
