"""Deterministic fictional event activity. No real names or attendee identifiers."""
from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

import pandas as pd


def generate_demo(seed: int = 2026) -> dict[str, pd.DataFrame]:
    """Create 18 imaginary sessions with registration and check-in observations."""
    rng = Random(seed)
    tracks = ["Data", "Engineering", "Product"]
    topics = {
        "Data": ["Analytics for Decisions", "Practical BI"],
        "Engineering": ["API Design", "Reliable Automation"],
        "Product": ["Service Design", "Operational Excellence"],
    }
    first_day = datetime(2026, 5, 14)
    sessions, registrations, checkins = [], [], []
    serial = 0
    for day in range(3):
        event_day = (first_day + timedelta(days=day)).date()
        for track_index, track in enumerate(tracks):
            for slot in range(2):
                sid = f"DEMO-S{day + 1}{track_index + 1}{slot + 1}"
                capacity = rng.choice([50, 70, 90, 110])
                sessions.append({
                    "session_id": sid,
                    "session_title": topics[track][slot],
                    "event_date": event_day.isoformat(),
                    "track": track,
                    "capacity": capacity,
                })
                registered = round(capacity * rng.uniform(0.62, 1.08))
                arrivals = min(capacity, round(registered * rng.uniform(0.54, 0.91)))
                for index in range(registered):
                    serial += 1
                    rid = f"DEMO-R{serial:05d}"
                    registration_time = first_day - timedelta(days=rng.randint(5, 36),
                                                              hours=rng.randint(0, 22))
                    registrations.append({
                        "registration_id": rid,
                        "session_id": sid,
                        "registered_at": registration_time.isoformat(),
                        "channel": rng.choices(["Web", "Referral", "Email"], weights=[5, 3, 2])[0],
                    })
                    if index < arrivals:
                        checkins.append({
                            "checkin_id": f"DEMO-C{serial:05d}",
                            "registration_id": rid,
                            "checked_in_at": datetime.combine(event_day, datetime.min.time())
                                .replace(hour=9 + slot * 3).isoformat(),
                            "method": rng.choices(["QR", "Manual"], weights=[9, 1])[0],
                        })
    return {
        "sessions": pd.DataFrame(sessions),
        "registrations": pd.DataFrame(registrations),
        "checkins": pd.DataFrame(checkins),
    }
