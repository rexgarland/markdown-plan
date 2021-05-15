"""
This module handles the internal gantt representations of event time and duration, defining operators like + and - when appropriate.
"""

import datetime as dt

from . import utils
from . import parse
from .settings import WORK_HOURS, WEEKEND

TODAY = dt.date.today()
NOW = dt.datetime.now()

WEEK_MAPPING = {
    'mon': 0,
    'tue': 1,
    'wed': 2,
    'thu': 3,
    'fri': 4,
    'sat': 5,
    'sun': 6,
}

class GanttScale:
    def __init__(self):
        self._work_hours = sorted(WORK_HOURS)
        self._weekend_indices = sorted([WEEK_MAPPING[w] for w in WEEKEND])
        self._workday_indices = [i for i in range(7) if not i in self._weekend_indices]
        self._hpd = len(self._work_hours)
        self._dpw = len(self._workday_indices)

    def time_to_hours_since_morning(self, time):
        full_hours = len([h for h in self._work_hours if h<time.hour])
        partial = dt.datetime.combine(TODAY, time)-dt.datetime.combine(TODAY, dt.time(time.hour))
        hours = full_hours + partial.total_seconds()/3600.0
        return hours

    def hours_since_morning_to_time(self, hours):
        assert hours<=self._hpd
        hour = self._work_hours[int(hours)]
        partial = dt.datetime.combine(TODAY, dt.time(hour=hour)) + dt.timedelta(seconds=(hours-int(hours))*3600)
        return partial.time()

    def workdays_to_calendar_days(self, datetime, workdays):
        assert int(workdays)==workdays
        index = datetime.weekday()
        calendar_days = 0
        if workdays>=0:
            while index in self._weekend_indices:
                index = (index+1) % 7
                calendar_days += 1
            while workdays>0:
                index = (index+1) % 7
                calendar_days += 1
                if not (index in self._weekend_indices):
                    workdays -= 1
            return calendar_days
        else:
            while index in self._weekend_indices:
                index = (index-1) % 7
                calendar_days -= 1
            while workdays<0:
                index = (index-1) % 7
                calendar_days -= 1
                if not (index in self._weekend_indices):
                    workdays += 1
            return calendar_days

    def during_work(self, datetime):
        if datetime.date().weekday() in self._weekend_indices:
            return False
        return datetime.hour in self._work_hours

    def soonest_workday(self, date):
        upcoming_week = [((date.weekday()+addition) % 7, addition) for addition in range(7)]
        days_to_next_workday = [addition for (i, addition) in upcoming_week if i in self._workday_indices][0]
        return date + dt.timedelta(days=days_to_next_workday)

    def soonest_work(self, datetime):
        if self.during_work(datetime):
            return datetime
        if not (datetime.date().weekday() in self._workday_indices):
            date = self.soonest_workday(datetime.date())
            return dt.datetime.combine(date, dt.time(min(self._work_hours)))
        else:
            remaining_hours = [h for h in self._work_hours if h>datetime.hour]
            if not remaining_hours:
                date = self.soonest_workday(datetime.date()+dt.timedelta(days=1))
                return dt.datetime.combine(date, dt.time(min(self._work_hours)))
            return dt.datetime.combine(datetime.date(), dt.time(remaining_hours[0]))

    def add_hours(self, datetime, hours):
        result = self.soonest_work(datetime)
        full_weeks = abs(hours)//(self._hpd*self._dpw) * (-1)**(hours<0)
        result += dt.timedelta(days=7*full_weeks)
        hours -= full_weeks*self._hpd*self._dpw
        full_days = abs(hours)//(self._hpd) * (-1)**(hours<0)
        calendar_days = self.workdays_to_calendar_days(result, full_days)
        result += dt.timedelta(days=calendar_days)
        hours -= full_days*self._hpd
        day_position = self.time_to_hours_since_morning(result.time()) + hours
        shift_days = day_position//self._hpd
        result += dt.timedelta(days=self.workdays_to_calendar_days(result, shift_days))
        remainder = day_position % self._hpd
        time = self.hours_since_morning_to_time(remainder)
        return dt.datetime.combine(result.date(), time)

    def datetime_interval_to_hours(self, d1, d2):
        result = self.soonest_work(d1)
        days = (d2-result).days
        full_weeks = abs(days)//7 * (-1)**(days<0)
        hours = self._dpw*self._hpd*full_weeks
        result = result + dt.timedelta(days=7*full_weeks)
        # now we're at the same week
        step = (-1)**(result>d2)
        while result.date()!=d2.date():
            result += dt.timedelta(days=step)
            if result.weekday() in self._workday_indices:
                hours += self._hpd*step
        # now we're on the same day
        result_hour = self.time_to_hours_since_morning(result.time())
        dest_hour = self.time_to_hours_since_morning(d2.time())
        hours += dest_hour-result_hour
        return hours

class GanttEvent(GanttScale):
    '''
    Interface for moments on a gantt timeline.

    Creates:
        - hours
    '''

    def __init__(self, obj=None, hours=None, date=None, time=None, datetime=None, **kwargs):
        super().__init__(**kwargs)
        specified = bool(obj)+bool(date)+bool(time)+bool(datetime)+bool(hours)
        assert specified, "Underspecified GanttEvent: must provide datetime, date, time, or hours"
        assert specified==1, "Overspecified GanttEvent: use datetime, date, time, or hours (not any combination)."
        if obj:
            self.parse_object(obj)
        else:
            self.hours = hours
            self.date = date
            self.time = time
            self.datetime = datetime

    def parse_object(self, obj):
        try:
            self.hours = float(obj)
        except (ValueError, TypeError):
            if type(obj) is str:
                self.parse_object(parse.parse_time(obj))
            else:
                if utils.is_date(obj):
                    self.date = obj
                elif utils.is_time(obj):
                    self.time = obj
                elif utils.is_datetime(obj):
                    self.datetime = obj
                else:
                    raise ValueError(f"Input of type '{type(obj)}' is not a recognized event type.")

    def normalize(self):
        self._datetime = self.soonest_work(self._datetime)
        self._date = self._datetime.date()
        self._time = self._datetime.time()

    @property
    def hours(self):
        return self._hours

    @hours.setter
    def hours(self, value):
        if value is None:
            return
        self._hours = value
        self._datetime = self.add_hours(NOW, self._hours)
        self._date = self._datetime.date()
        self._time = self._datetime.time()
        self.normalize()

    @property
    def datetime(self):
        return self._datetime

    @datetime.setter
    def datetime(self, value):
        if value is None:
            return
        self._datetime = value
        self._date = self._datetime.date()
        self._time = self._datetime.time()
        self._hours = self.datetime_interval_to_hours(NOW, self._datetime)
        self.normalize()

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        if value is None:
            return
        self._date = value
        self._time = dt.time(hour=min(self._work_hours))
        self._datetime = dt.datetime.combine(self._date, self._time)
        self._hours = self.datetime_interval_to_hours(NOW, self._datetime)
        self.normalize()

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        if value is None:
            return
        self._time = value
        self._date = TODAY
        self._datetime = dt.datetime.combine(self._date, self._time)
        self._hours = self.datetime_interval_to_hours(NOW, self._datetime)
        self.normalize()

    def __add__(self, gantt_interval):
        newdatetime = self.add_hours(self.datetime, gantt_interval.hours)
        return GanttEvent(datetime=newdatetime)

    def __sub__(self, gantt_interval):
        newdatetime = self.add_hours(self.datetime, -gantt_interval.hours)
        return GanttEvent(datetime=newdatetime)

    def __lt__(self, other):
        return self.datetime<other.datetime

    def __le__(self, other):
        return self.datetime<=other.datetime

class GanttDuration(GanttScale):
    '''
    Interface for classes requiring gantt timeline utilities.

    Subclasses must implement:
        - scale (one of minutes, hours, days, weeks, months)
        - value (float)

    Creates:
        - hours
    '''

    def __init__(self, value=0, scale='hours', **kwargs):
        super().__init__(**kwargs)
        self._scale = scale
        self.value = value

    @property
    def hours(self):
        if self._scale=='months':
            factor = self._hpd*self._dpw*4
        elif self._scale=='weeks':
            factor = self._hpd*self._dpw
        elif self._scale=='days':
            factor = self._hpd
        elif self._scale=='hours':
            factor = 1
        elif self._scale=='minutes':
            factor = 1.0/60
        else:
            raise Exception(f'Scale for gantt interval not recognized: {self._scale}')
        return self.value*factor

    def __gt__(self, other):
        return self.hours>other.hours

    def __add__(self, other):
        if hasattr(other, 'hours'):
            total_hours = self.hours+other.hours
            return GanttDuration(scale='hours', value=total_hours)
        elif other==0:
            return self
        else:
            raise ValueError(f'Unrecognized type {type(other)} for addition to GanttDuration')

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if hasattr(other, 'hours'):
            total_hours = self.hours-other.hours
            return GanttDuration(scale='hours', value=total_hours)
        elif other==0:
            return self
        else:
            raise ValueError(f'Unrecognized type {type(other)} for subtraction from GanttDuration')

    def __neg__(self):
        return GanttDuration(scale='hours', value=-self.hours)

    def __rsub__(self, other):
        neg = self.__sub__(other)
        return GanttDuration(scale='hours', value=-neg.hours)

    def __repr__(self):
        hours = self.hours
        if hours<self._hpd:
            return f"{hours:.2f} hours"
        days = float(hours)/self._hpd
        if days<self._dpw:
            return f"{days:.2f} days"
        weeks = float(days)/self._dpw
        if weeks<8:
            return f"{weeks:.2f} weeks"
        months = float(weeks)/4
        return f"{months:.2f} months"
    