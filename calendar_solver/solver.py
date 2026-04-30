import datetime

def is_weekend(date: datetime.date) -> bool:
    """Return True if date falls on Saturday or Sunday."""
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday

def get_us_federal_holidays(year: int) -> set[datetime.date]:
    """Return a set of US federal public holiday dates for the given year.
    Hardcode the 11 federal holidays. Account for observed dates
    (e.g. if July 4 falls on Sunday, observed Monday is the holiday)."""
    holidays = set()
    # New Year's Day
    new_years_day = datetime.date(year, 1, 1)
    if new_years_day.weekday() == 5:  # Saturday
        holidays.add(new_years_day - datetime.timedelta(days=1))  # Observed on Friday
    elif new_years_day.weekday() == 6:  # Sunday
        holidays.add(new_years_day + datetime.timedelta(days=1))  # Observed on Monday
    else:
        holidays.add(new_years_day)
    # Martin Luther King, Jr. Day (3rd Monday in January)
    mlk_day = datetime.date(year, 1, 1) + datetime.timedelta(days=(7 - datetime.date(year, 1, 1).weekday()) % 7 + 14)
    holidays.add(mlk_day)
    # President's Day (3rd Monday in February)
    presidents_day = datetime.date(year, 2, 1) + datetime.timedelta(days=(7 - datetime.date(year, 2, 1).weekday()) % 7 + 14)
    holidays.add(presidents_day)
    # Memorial Day (last Monday in May)
    memorial_day = datetime.date(year, 5, 31) - datetime.timedelta(days=datetime.date(year, 5, 31).weekday())
    holidays.add(memorial_day)
    # Juneteenth National Independence Day (June 19)
    juneteenth = datetime.date(year, 6, 19)
    if juneteenth.weekday() == 5:  # Saturday
        holidays.add(juneteenth - datetime.timedelta(days=1))  # Observed on Friday
    elif juneteenth.weekday() == 6:  # Sunday
        holidays.add(juneteenth + datetime.timedelta(days=1))  # Observed on Monday
    else:
        holidays.add(juneteenth)
    # Independence Day (July 4)
    independence_day = datetime.date(year, 7, 4)
    if independence_day.weekday() == 5:  # Saturday
        holidays.add(independence_day - datetime.timedelta(days=1))  # Observed on Friday
    elif independence_day.weekday() == 6:  # Sunday
        holidays.add(independence_day + datetime.timedelta(days=1))  # Observed on Monday
    else:
        holidays.add(independence_day)
    # Labor Day (1st Monday in September)
    labor_day = datetime.date(year, 9, 1) + datetime.timedelta(days=(7 - datetime.date(year, 9, 1).weekday()) % 7)
    holidays.add(labor_day)
    # Columbus Day (2nd Monday in October)
    columbus_day = datetime.date(year, 10, 1) + datetime.timedelta(days=(7 - datetime.date(year, 10, 1).weekday()) % 7 + 7)
    holidays.add(columbus_day)
    # Veterans Day (November 11)
    veterans_day = datetime.date(year, 11, 11)
    if  veterans_day.weekday() == 5:  # Saturday
        holidays.add(veterans_day - datetime.timedelta(days=1))  # Observed on Friday
    elif veterans_day.weekday() == 6:  # Sunday
        holidays.add(veterans_day + datetime.timedelta(days=1))  # Observed on Monday
    else:
        holidays.add(veterans_day)
    # Thanksgiving (4th Thursday in November)
    thanksgiving = datetime.date(year, 11, 1) + datetime.timedelta(days=(3 - datetime.date(year, 11, 1).weekday()) % 7 + 21)
    holidays.add(thanksgiving)
    # Christmas (December 25)
    christmas = datetime.date(year, 12, 25)
    if christmas.weekday() == 5:  # Saturday
        holidays.add(christmas - datetime.timedelta(days=1))  # Observed on Friday
    elif christmas.weekday() == 6:  # Sunday
        holidays.add(christmas + datetime.timedelta(days=1))  # Observed on Monday
    else:
        holidays.add(christmas)

    return holidays

def is_vacation_day(date: datetime.date, holidays: set[datetime.date]) -> bool:
    """Return True if date costs a vacation day
    (i.e. it is a weekday and not a federal holiday)."""
    return not is_weekend(date) and date not in holidays

def count_vacation_days(start: datetime.date, end: datetime.date, holidays: set[datetime.date]) -> int:
    """Count how many vacation days are consumed between start and end (inclusive).
    Weekends and holidays are free."""
    vacation_days = 0
    current_date = start
    while current_date <= end:
        if is_vacation_day(current_date, holidays):
            vacation_days += 1
        current_date += datetime.timedelta(days=1)
    return vacation_days