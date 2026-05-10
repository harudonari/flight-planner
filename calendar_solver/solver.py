import datetime
from dataclasses import dataclass
from typing import Any
from itertools import combinations

@dataclass
class Window:
    trip_id: str
    start_date: datetime.date
    end_date: datetime.date
    total_days: int
    vacation_days_cost: int
    weekend_anchored: bool
    overlaps_holiday: bool
    score: float | None = None

@dataclass
class CombinedPlan:
    windows: list[Window]       # one window per trip
    total_vacation_days: int
    total_score: float          # average of individual window scores

@dataclass
class TripConstraint:
    id: str
    destination: str
    departure_cities: list[str]
    min_duration_days: int

@dataclass
class SolverConstraints:
    vacation_days_remaining: int
    year: int
    trips: list[TripConstraint]
    blackout_dates: set[datetime.date]
    earliest_start: datetime.date
    latest_end: datetime.date
    max_trips: int | None

def solve(constraints: dict, config: dict = {}) -> dict:
    """Main entry point.
    1. Parse constraints
    2. Compute holidays
    3. Generate windows per trip
    4. Score and rank windows per trip
    5. Find non-overlapping combinations
    6. Return structured output (see below)
    """
    try:
        parsed_constraints = parse_constraints(constraints)
        holidays = get_us_federal_holidays(parsed_constraints.year)

        windows_by_trip = {}
        windows_count = 0
        for trip in parsed_constraints.trips:
            windows = generate_windows(trip, parsed_constraints, holidays)
            windows_count += len(windows)
            reranked = rank_windows(windows, parsed_constraints)
            windows_by_trip[trip.id] = reranked

        combined_plan, combinations_evaluated = find_non_overlapping_combinations(windows_by_trip, parsed_constraints.vacation_days_remaining)
        return {
            "status": "ok",
            "trips": {
                trip_id: [
                    {
                        "trip_id": w.trip_id,
                        "start_date": str(w.start_date),
                        "end_date": str(w.end_date),
                        "vacation_days_cost": w.vacation_days_cost,
                        "weekend_anchored": w.weekend_anchored,
                        "overlaps_holiday": w.overlaps_holiday,
                        "score": w.score
                    }
                    for w in windows
                ]
                for trip_id, windows in windows_by_trip.items()
            },
            "combined_plans": [
                {
                    "windows": [
                        {
                            "trip_id": w.trip_id,
                            "start_date": str(w.start_date),
                            "end_date": str(w.end_date),
                            "vacation_days_cost": w.vacation_days_cost,
                            "weekend_anchored": w.weekend_anchored,
                            "overlaps_holiday": w.overlaps_holiday,
                            "score": w.score
                        }
                        for w in plan.windows
                    ],
                    "total_vacation_days": plan.total_vacation_days,
                    "total_score": plan.total_score
                }
                for plan in combined_plan
            ],
            "metadata": {
                "total_windows_generated": windows_count,
                "combinations_evaluated": combinations_evaluated,
                "combinations_returned": len(combined_plan)
            }
        }

    except ValueError as e: 
        return {
            "status": "error",
            "message": str(e)
        }

def _overlaps_any(candidate: Window, selected: list[Window]) -> bool:
    for window in selected:
        if candidate.start_date <= window.end_date and window.start_date <= candidate.end_date:
            return True
    return False

def find_non_overlapping_combinations(
    windows_by_trip: dict[str, list[Window]],
    vacation_days_remaining: int
) -> tuple[list[CombinedPlan], int]:
    """Find all combinations of windows (one per trip) where:
    - No two windows overlap in calendar dates
    - Combined vacation_days_cost <= vacation_days_remaining
    Return combinations sorted by total_score descending.
    Cap output at 20 combinations to keep response size reasonable."""

    trip_ids = list(windows_by_trip.keys())
    all_plans = []
    current_selection = []
    combinations_evaluated = 0

    def backtrack(trip_index: int, budget_remaining: int):
        nonlocal combinations_evaluated # nonlocal keyword tells Python to use the variable found in the nearest enclosing scope
        if trip_index == len(trip_ids):
            combinations_evaluated += 1
            # a window is chosen for all trips, meaning a valid plan
            total_score = sum(window.score or 0.0 for window in current_selection) / len(current_selection)
            total_days = sum(window.vacation_days_cost for window in current_selection)

            if len(all_plans) < 20 or total_score > all_plans[-1].total_score:
                all_plans.append(CombinedPlan(
                    windows=list(current_selection),
                    total_vacation_days=total_days,
                    total_score=total_score
                ))
                all_plans.sort(key=lambda p: p.total_score, reverse=True)
                if len(all_plans) > 20:
                    all_plans.pop() # drop the lowest scoring window
            return
        
        trip_id = trip_ids[trip_index]
        for window in windows_by_trip[trip_id]:
            if window.vacation_days_cost > budget_remaining: # window not valid, move on to next
                continue
            if _overlaps_any(window, current_selection): # window not valid, move on to next
                continue
        
            current_selection.append(window)
            backtrack(trip_index + 1, vacation_days_remaining - window.vacation_days_cost)
            current_selection.pop()  # all of trip_index+1 trip is checked, check the next window for trip_index trip

    backtrack(0, vacation_days_remaining)

    return all_plans, combinations_evaluated


def find_non_overlapping_combinations_recursion(
    windows_by_trip: dict[str, list[Window]],
    vacation_days_remaining: int,
    combined_plans: list[CombinedPlan],
    earliest_start: datetime.date,
    latest_end: datetime.date,
    combinations_evaluated: list[int]
) -> list[CombinedPlan]:
    """Find all combinations of windows (one per trip) where:
    - No two windows overlap in calendar dates
    - Combined vacation_days_cost <= vacation_days_remaining
    Return combinations sorted by total_score descending.
    Cap output at 20 combinations to keep response size reasonable."""


    # base case: 20 combinations already in the list
    if len(combined_plans) >= 20:
        return combined_plans
    
    # base case: one of the windows list is empty
    shortest_key = min(windows_by_trip, key=lambda k: len(windows_by_trip[k]))
    shortest_list = windows_by_trip[shortest_key]

    if len(shortest_list) == 0:
        return combined_plans

    # base case: Running vacation cost exceeds budget
    vacation_days_cost_total = sum(windows_by_trip[k][0].vacation_days_cost for k in windows_by_trip)
    
    if vacation_days_cost_total > vacation_days_remaining:
        return combined_plans
    
    first_windows = [windows[0] for windows in windows_by_trip.values()]
    combinations_evaluated[0] += 1
    for a, b in combinations(first_windows, 2):
        if a.start_date <= b.end_date and b.start_date <= a.end_date:
            # Remove the overlapped window from a and call the function
            new_dict_a = {key: (value[1:] if key == a.trip_id else value) for key, value in windows_by_trip.items()}
            find_non_overlapping_combinations_recursion(new_dict_a, vacation_days_remaining, combined_plans, earliest_start, latest_end, combinations_evaluated)

            # Remove the overlapped window from b and call the function
            new_dict_b = {key: (value[1:] if key == b.trip_id else value) for key, value in windows_by_trip.items()}
            find_non_overlapping_combinations_recursion(new_dict_b, vacation_days_remaining, combined_plans, earliest_start, latest_end, combinations_evaluated)

            return combined_plans

    # No overlap found, create plan and add it to combined_plans
    total_score = sum(w.score or 0.0 for w in first_windows) / len(first_windows)


    plan = CombinedPlan(
        windows=first_windows,
        total_vacation_days=vacation_days_cost_total,
        total_score=total_score
    )
    combined_plans.append(plan)

    # Move on to the next iteration of score calculating by removing the first items in all of the windows list
    new_dict = {key: value[1:] for key, value in windows_by_trip.items()}
    vacation_days_remaining_updated = vacation_days_remaining - vacation_days_cost_total
    find_non_overlapping_combinations_recursion(new_dict, vacation_days_remaining_updated, combined_plans, earliest_start, latest_end, combinations_evaluated)

    return combined_plans

def is_weekend_anchored(start: datetime.date, end: datetime.date) -> bool:
    """Return True if the window starts on Fri/Sat OR ends on Sun/Mon."""
    return start.weekday() in (4, 5) or end.weekday() in (6, 0)

def generate_windows(
    trip: TripConstraint,
    constraints: SolverConstraints,
    holidays: set[datetime.date],
) -> list[Window]:
    """Generate all valid windows for a single trip.
    A window is valid if:
    - Total calendar length >= trip.min_duration_days
    - No date in the window is in constraints.blackout_dates
    - Window falls within [earliest_start, latest_end]
    - vacation_days_cost > 0 is acceptable (pruning against budget happens later)
    """
    windows = []

    pointer = constraints.earliest_start
    # while earliest_start + min_duration - 1 <= latest_end:
    while pointer + datetime.timedelta(days=trip.min_duration_days - 1) <= constraints.latest_end:
        window_start = pointer
        window_end = pointer + datetime.timedelta(days=trip.min_duration_days - 1)
        window_pointer = window_start

        window_overlaps_holiday = False
        window_vacation_days_cost = 0
        break_due_to_blackout = False

        while window_pointer <= window_end:
            if window_pointer in constraints.blackout_dates:
                break_due_to_blackout = True
                break
            
            if is_vacation_day(window_pointer, holidays):
                window_vacation_days_cost += 1
            if window_pointer in holidays:
                window_overlaps_holiday = True
            
            window_pointer += datetime.timedelta(days=1)
    
        if break_due_to_blackout:
            # Move pointer to the day after the blackout date and restart
            pointer = window_pointer + datetime.timedelta(days=1)
        else:
            windows.append(Window(
                trip_id=trip.id,
                start_date=window_start,
                end_date=window_end,
                total_days=trip.min_duration_days,
                vacation_days_cost=window_vacation_days_cost,
                weekend_anchored=is_weekend_anchored(window_start, window_end),
                overlaps_holiday=window_overlaps_holiday,
            ))
            pointer += datetime.timedelta(days=1)

    return windows

def score_window(window: Window, earliest_start: datetime.date, latest_end: datetime.date) -> float:
    """Return a score between 0.0 and 1.0. Higher is better.

    Scoring components (weights are suggestions — tune as you see fit):
    - Vacation efficiency (50%): vacation_days_cost / total_days, inverted
      so lower cost = higher score
    - Weekend anchoring (40%): 1.0 if anchored, 0.0 if not
    - Lead time bonus (10%): earlier start dates score marginally higher
      (normalized within the search window)

    Clamp final score to [0.0, 1.0].
    """
    vacation_efficiency = 1 - window.vacation_days_cost / window.total_days
    weekend_score = 1.0 if window.weekend_anchored else 0.0
    # For lead time, we can give a small bonus for starting earlier in the year
    total_search_days = (latest_end - earliest_start).days + 1
    lead_time_score = 1 - (window.start_date - earliest_start).days / total_search_days

    raw_score = 0.5 * vacation_efficiency + 0.4 * weekend_score + 0.1 * lead_time_score
    return max(0.0, min(1.0, raw_score))

def rank_windows(windows: list[Window], constraints: SolverConstraints) -> list[Window]:
    """Attach scores to all windows and return them sorted descending by score.
    Also prune any windows whose vacation_days_cost exceeds
    constraints.vacation_days_remaining."""
    for window in windows:
        if window.vacation_days_cost <= constraints.vacation_days_remaining:
            window.score = score_window(window, constraints.earliest_start, constraints.latest_end)
    pruned = [w for w in windows if w.score is not None]
    pruned.sort(key=lambda x: x.score or 0.0, reverse=True)
    return pruned

def _require(raw: dict[str, Any], field: str) -> Any:
    if field not in raw:
        raise ValueError(f"Missing required field: {field}")
    return raw[field]

def parse_constraints(raw: dict) -> SolverConstraints:
    """Parse and validate the raw input dict. Raises ValueError for any missing or invalid field."""
    vacation_days_remaining = _require(raw, 'vacation_days_remaining')
    if not isinstance(vacation_days_remaining, int) or isinstance(vacation_days_remaining, bool) or vacation_days_remaining < 0:
        raise ValueError("vacation_days_remaining must be a non-negative integer")

    year = _require(raw, 'year')
    if not isinstance(year, int) or isinstance(year, bool) or not 1900 < year < datetime.datetime.now().year + 10:
        raise ValueError("year must be a valid year between 1900 and 10 years from now")

    trips_raw = _require(raw, 'trips')
    if not isinstance(trips_raw, list) or not trips_raw:
        raise ValueError("trips must be a list of trip constraints")

    trips = []
    seen_ids = set()
    for trip_raw in trips_raw:
        trip_id = _require(trip_raw, 'id')
        if trip_id in seen_ids:
            raise ValueError(f"Duplicate trip id: {trip_id}")
        seen_ids.add(trip_id)

        destination = _require(trip_raw, 'destination')
        if not destination:
            raise ValueError(f"Trip {trip_id} has an empty destination")

        departure_cities = _require(trip_raw, 'departure_cities')
        if not isinstance(departure_cities, list) or not departure_cities:
            raise ValueError(f"Trip {trip_id} must have a non-empty list of departure cities")

        min_duration_days = _require(trip_raw, 'min_duration_days')
        if not isinstance(min_duration_days, int) or isinstance(min_duration_days, bool) or min_duration_days <= 0:
            raise ValueError(f"Trip {trip_id} must have a positive integer min_duration_days")

        trips.append(TripConstraint(id=trip_id, destination=destination, departure_cities=departure_cities, min_duration_days=min_duration_days))

    # Optional — no blackout dates is a valid state
    blackout_dates_raw = raw.get('blackout_dates', [])
    if not isinstance(blackout_dates_raw, list):
        raise ValueError("blackout_dates must be a list of date strings in YYYY-MM-DD format")
    blackout_dates = set()
    for date_str in blackout_dates_raw:
        try:
            blackout_dates.add(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            raise ValueError(f"Invalid date format for blackout_date '{date_str}': expected YYYY-MM-DD")

    earliest_start_str = _require(raw, 'earliest_start')
    try:
        earliest_start = datetime.datetime.strptime(earliest_start_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format for earliest_start '{earliest_start_str}': expected YYYY-MM-DD")

    latest_end_str = _require(raw, 'latest_end')
    try:
        latest_end = datetime.datetime.strptime(latest_end_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format for latest_end '{latest_end_str}': expected YYYY-MM-DD")

    if earliest_start >= latest_end:
        raise ValueError("earliest_start must be before latest_end")

    max_trips = raw.get('max_trips')
    if max_trips is not None:
        if not isinstance(max_trips, int) or isinstance(max_trips, bool) or max_trips <= 0:
            raise ValueError("max_trips must be a positive integer if provided")

    return SolverConstraints(
        vacation_days_remaining=vacation_days_remaining,
        year=year,
        trips=trips,
        blackout_dates=blackout_dates,
        earliest_start=earliest_start,
        latest_end=latest_end,
        max_trips=max_trips,
    )

def is_weekend(date: datetime.date) -> bool:
    """Return True if date falls on Saturday or Sunday."""
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday

def _observed(date: datetime.date) -> datetime.date:
    """Helper function for calculating observed holidays when it falls onto weekends."""
    if date.weekday() == 5: # Saturday
        return date - datetime.timedelta(days=1) # Observed on Friday
    if date.weekday() == 6: # Sunday
        return date + datetime.timedelta(days=1) # Observed on Monday
    return date

def get_us_federal_holidays(year: int) -> set[datetime.date]:
    """Return a set of US federal public holiday dates for the given year.
    Hardcode the 11 federal holidays. Account for observed dates
    (e.g. if July 4 falls on Sunday, observed Monday is the holiday)."""
    holidays = set()
    # New Year's Day (January 1st)
    new_years_day = _observed(datetime.date(year, 1, 1))
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
    juneteenth = _observed(datetime.date(year, 6, 19))
    holidays.add(juneteenth)
    # Independence Day (July 4)
    independence_day = _observed(datetime.date(year, 7, 4))
    holidays.add(independence_day)
    # Labor Day (1st Monday in September)
    labor_day = datetime.date(year, 9, 1) + datetime.timedelta(days=(7 - datetime.date(year, 9, 1).weekday()) % 7)
    holidays.add(labor_day)
    # Columbus Day (2nd Monday in October)
    columbus_day = datetime.date(year, 10, 1) + datetime.timedelta(days=(7 - datetime.date(year, 10, 1).weekday()) % 7 + 7)
    holidays.add(columbus_day)
    # Veterans Day (November 11)
    veterans_day = _observed(datetime.date(year, 11, 11))
    holidays.add(veterans_day)
    # Thanksgiving (4th Thursday in November)
    thanksgiving = datetime.date(year, 11, 1) + datetime.timedelta(days=(3 - datetime.date(year, 11, 1).weekday()) % 7 + 21)
    holidays.add(thanksgiving)
    # Christmas (December 25)
    christmas = _observed(datetime.date(year, 12, 25))
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