"""
scheduler_service.py
---------------------
Generates a personalized day-by-day study timetable.

This feature does NOT call the AI. Building a schedule is a math/logic
problem (dates, proportional hour allocation) -- a deterministic Python
algorithm gives correct, predictable results every time, unlike an LLM
which could make date-arithmetic mistakes.
"""

from datetime import date, timedelta

# Higher priority = more weight = more study hours allocated
PRIORITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3
}


def generate_timetable(subjects, hours_per_day):
    """
    subjects: list of dicts like:
        {"name": "Math", "exam_date": "2026-08-15", "priority": "high"}
    hours_per_day: number, total study hours available each day

    Returns a day-by-day schedule:
        [{"date": "...", "day_name": "...", "allocations": [{"subject": "...", "hours": 2.0}]}]
    """
    today = date.today()

    # ---- Step 1: parse & validate, drop subjects whose exam already passed ----
    parsed_subjects = []
    for subj in subjects:
        try:
            exam_date = date.fromisoformat(subj["exam_date"])
        except (ValueError, KeyError, TypeError):
            raise ValueError(f"Invalid exam_date for subject '{subj.get('name', '?')}'. Use YYYY-MM-DD.")

        if exam_date < today:
            continue  # skip subjects whose exam already happened

        parsed_subjects.append({
            "name": subj["name"],
            "exam_date": exam_date,
            "priority": subj.get("priority", "medium")
        })

    if not parsed_subjects:
        raise ValueError("No valid upcoming subjects to schedule. Check your exam dates.")

    # ---- Step 2: the schedule runs from today until the latest exam date ----
    last_exam_date = max(s["exam_date"] for s in parsed_subjects)
    total_days = (last_exam_date - today).days + 1

    schedule = []

    for day_offset in range(total_days):
        current_day = today + timedelta(days=day_offset)

        # Only subjects whose exam hasn't happened yet get studied today
        active_subjects = [s for s in parsed_subjects if s["exam_date"] >= current_day]
        if not active_subjects:
            continue

        # ---- Step 3: weight = priority × urgency ----
        # Urgency increases as the exam gets closer (1 / days_left),
        # so subjects with near exams naturally get more hours over time.
        weighted = []
        for s in active_subjects:
            days_left = max((s["exam_date"] - current_day).days, 1)
            priority_weight = PRIORITY_WEIGHTS.get(s["priority"], 2)
            urgency = 1 / days_left
            weighted.append({"name": s["name"], "weight": priority_weight * urgency})

        total_weight = sum(w["weight"] for w in weighted)

        # ---- Step 4: distribute today's hours proportionally ----
        allocations = []
        for w in weighted:
            share = w["weight"] / total_weight
            hours = round(hours_per_day * share * 2) / 2  # round to nearest 0.5 hr
            if hours > 0:
                allocations.append({"subject": w["name"], "hours": hours})

        schedule.append({
            "date": current_day.isoformat(),
            "day_name": current_day.strftime("%A"),
            "allocations": allocations
        })

    return schedule