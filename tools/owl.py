#!/usr/bin/env python3
"""Owl's storage. Keeps the profile, weekly plans, daily check-ins and notes in ../data as JSON.

Standard library only, Python 3.9+. Read commands print JSON. Write commands take one JSON
object on stdin and print what was saved. Errors are one plain sentence on stderr, exit code 1.

  status        where things stand: setup done? plan for this week? checked in today?
  profile       show the profile
  profile-set   merge keys into the profile (a null value removes the key)
  week          show a week's plan            [--week 2026-W46]
  week-set      agree or change a week's plan [--week ...] [--replace]
  checkin       save or correct one day's values
  view          everything needed for a reply [--days 14]
  note-add      remember a pattern, advice, question, fact or wish
  note-close    close a note with what came of it

Every command accepts --today YYYY-MM-DD (used for testing).
"""
import argparse
import json
import os
import re
import statistics
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("OWL_DATA") or HOME / "data")

# A check-in typed after midnight still belongs to the day that just ended.
DAY_ENDS_AT_HOUR = 5

FIELD_TYPES = ("number", "scale", "yesno", "text")
NOTE_KINDS = ("pattern", "advice", "question", "fact", "wish")
PROFILE_KEYS = (
    "name", "language", "tone", "set_up_by", "goals", "fields", "rules",
    "rhythm", "wishes", "open_questions", "onboarding",
)
PLAN_KEYS = (
    "capacity_hours", "main", "second", "rest_hours", "outward_step",
    "not_doing", "caps", "signals", "notes",
)
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
YES = ("yes", "y", "true", "да", "д")
NO = ("no", "n", "false", "нет", "н")


class OwlError(Exception):
    pass


# ---------- files ----------

def load(name, default):
    path = DATA / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        raise OwlError("the file data/%s is damaged and can't be read. Nothing was changed." % name)


def save(name, value):
    DATA.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=str(DATA), prefix=name + ".", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
        os.replace(temp, str(DATA / name))
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise


def read_input():
    raw = sys.stdin.buffer.read().decode("utf-8-sig").strip()
    if not raw:
        raise OwlError("this command needs a JSON object on standard input, and got nothing.")
    try:
        value = json.loads(raw)
    except ValueError as problem:
        raise OwlError("the input is not valid JSON (%s)." % problem)
    if not isinstance(value, dict):
        raise OwlError("the input must be one JSON object.")
    return value


def now_stamp():
    return datetime.now().isoformat(timespec="seconds")


# ---------- dates ----------

def parse_day(text):
    try:
        return datetime.strptime(str(text), "%Y-%m-%d").date()
    except ValueError:
        raise OwlError("'%s' is not a date. Use the form 2026-11-12." % text)


def current_day(args):
    if args.today:
        return parse_day(args.today)
    now = datetime.now()
    return (now - timedelta(days=1)).date() if now.hour < DAY_ENDS_AT_HOUR else now.date()


def week_id(day):
    year, week = day.isocalendar()[0], day.isocalendar()[1]
    return "%d-W%02d" % (year, week)


def week_days(day):
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def week_monday(week):
    if not re.match(r"^\d{4}-W\d{2}$", str(week)):
        raise OwlError("'%s' is not a week. Use the form 2026-W46." % week)
    try:
        return datetime.strptime(week + "-1", "%G-W%V-%u").date()
    except ValueError:
        raise OwlError("'%s' is not a real week." % week)


# ---------- profile ----------

def check_fields(fields):
    if not isinstance(fields, list):
        raise OwlError("'fields' must be a list.")
    seen = set()
    for field in fields:
        if not isinstance(field, dict) or "key" not in field:
            raise OwlError("each check-in field needs a 'key', for example {\"key\": \"hours\", \"type\": \"number\"}.")
        key = field["key"]
        if not re.match(r"^[a-z][a-z0-9_]*$", str(key)):
            raise OwlError("field key '%s' must be lowercase Latin letters, digits or underscores." % key)
        if key in seen:
            raise OwlError("field key '%s' is used twice." % key)
        seen.add(key)
        kind = field.setdefault("type", "text")
        if kind not in FIELD_TYPES:
            raise OwlError("field '%s' has type '%s'. Allowed types: %s." % (key, kind, ", ".join(FIELD_TYPES)))
        if kind == "scale":
            field.setdefault("min", 1)
            field.setdefault("max", 5)
            if not field["min"] < field["max"]:
                raise OwlError("field '%s': min must be below max." % key)


def cmd_profile(args):
    return load("profile.json", {})


def cmd_profile_set(args):
    patch = read_input()
    unknown = [key for key in patch if key not in PROFILE_KEYS]
    if unknown:
        raise OwlError("unknown profile key: %s. Allowed keys: %s." % (", ".join(unknown), ", ".join(PROFILE_KEYS)))
    if patch.get("fields") is not None:
        check_fields(patch["fields"])
    profile = load("profile.json", {})
    for key, value in patch.items():
        if value is None:
            profile.pop(key, None)
        elif key in ("rhythm", "onboarding") and isinstance(value, dict) and isinstance(profile.get(key), dict):
            profile[key].update(value)
        else:
            profile[key] = value
    profile["updated"] = now_stamp()
    save("profile.json", profile)
    return {"saved": sorted(patch), "profile": profile}


def fields_of(profile):
    return profile.get("fields") or []


# ---------- weekly plan ----------

def cmd_week(args):
    week = args.week or week_id(current_day(args))
    week_monday(week)
    entry = load("weeks.json", {}).get(week)
    if not entry:
        return {"week": week, "plan": None}
    return dict(entry, week=week)


def cmd_week_set(args):
    patch = read_input()
    week = args.week or week_id(current_day(args))
    week_monday(week)
    unknown = [key for key in patch if key not in PLAN_KEYS]
    if unknown:
        raise OwlError("unknown plan key: %s. Allowed keys: %s." % (", ".join(unknown), ", ".join(PLAN_KEYS)))
    for key in ("capacity_hours", "rest_hours"):
        if patch.get(key) is not None and not isinstance(patch[key], (int, float)):
            raise OwlError("'%s' must be a number of hours." % key)
    weeks = load("weeks.json", {})
    entry = weeks.get(week)
    if entry and not args.replace:
        plan = dict(entry["plan"])
        for key, value in patch.items():
            if value is None:
                plan.pop(key, None)
            else:
                plan[key] = value
    else:
        plan = {key: value for key, value in patch.items() if value is not None}
    if not isinstance(plan.get("main"), dict) or not plan["main"].get("name"):
        raise OwlError("a plan needs a main focus, for example {\"main\": {\"name\": \"...\", \"hours\": 15}}.")
    stamp = now_stamp()
    if entry:
        # Keep what was agreed before, so each day can be judged by the plan in force on that day.
        revisions = entry.get("revisions", [])
        revisions.append({"agreed": entry["agreed"], "until": stamp, "plan": entry["plan"]})
        entry = {"plan": plan, "agreed": stamp, "revisions": revisions}
    else:
        entry = {"plan": plan, "agreed": stamp, "revisions": []}
    weeks[week] = entry
    save("weeks.json", weeks)
    return {"saved": week, "changed_existing_plan": bool(entry["revisions"]), "plan": plan}


# ---------- check-ins ----------

def clean_value(field, value):
    key, kind = field["key"], field["type"]
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise OwlError("'%s' must be a number, zero or more." % key)
        return value
    if kind == "scale":
        low, high = field.get("min", 1), field.get("max", 5)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise OwlError("'%s' must be a number from %s to %s." % (key, low, high))
        return value
    if kind == "yesno":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in YES:
            return True
        if text in NO:
            return False
        raise OwlError("'%s' must be true or false." % key)
    return str(value).strip()


def cmd_checkin(args):
    incoming = read_input()
    profile = load("profile.json", {})
    fields = {field["key"]: field for field in fields_of(profile)}
    if not fields:
        raise OwlError("no check-in fields are set up yet. Finish setup first (profile-set with 'fields').")
    values = incoming.get("values")
    if not isinstance(values, dict) or not values:
        raise OwlError("the input needs 'values', for example {\"values\": {\"%s\": ...}}." % next(iter(fields)))
    unknown = [key for key in values if key not in fields]
    if unknown:
        raise OwlError("unknown check-in field: %s. This person's fields: %s." % (", ".join(unknown), ", ".join(fields)))
    today = current_day(args)
    day = parse_day(incoming["date"]) if incoming.get("date") else today
    if day > today:
        raise OwlError("%s is in the future. A check-in can only be for today or an earlier day." % day)

    days = load("days.json", {})
    entry = days.get(str(day), {"values": {}, "history": []})
    was_new = not entry["values"]
    stamp = now_stamp()
    changed = []
    for key, value in values.items():
        if value is None:
            continue
        cleaned = clean_value(fields[key], value)
        if key in entry["values"] and entry["values"][key] != cleaned:
            entry["history"].append({"at": stamp, "field": key, "was": entry["values"][key]})
            changed.append(key)
        entry["values"][key] = cleaned
    entry["updated"] = stamp
    days[str(day)] = entry
    save("days.json", days)
    return {
        "saved": str(day),
        "weekday": WEEKDAYS[day.weekday()],
        "new_day": was_new,
        "corrected": changed,
        "values": entry["values"],
        "missing": [key for key in fields if key not in entry["values"]],
    }


# ---------- reading ----------

def day_row(days, day, today):
    entry = days.get(str(day))
    row = {"date": str(day), "weekday": WEEKDAYS[day.weekday()]}
    if day > today:
        row["status"] = "future"
    elif entry and entry.get("values"):
        row["status"] = "checked_in"
        row["values"] = entry["values"]
    else:
        # No check-in means unknown. It is never a zero.
        row["status"] = "unknown"
    return row


def totals(rows, fields):
    result = {}
    for field in fields:
        if field["type"] != "number":
            continue
        numbers = [row["values"][field["key"]] for row in rows if row.get("values") and field["key"] in row["values"]]
        if numbers:
            result[field["key"]] = {"sum": round(sum(numbers), 2), "days_counted": len(numbers)}
    return result


def week_block(week_start, days, weeks, fields, today):
    rows = [day_row(days, day, today) for day in week_days(week_start)]
    entry = weeks.get(week_id(week_start))
    return {
        "week": week_id(week_start),
        "plan": entry["plan"] if entry else None,
        "plan_agreed": entry["agreed"] if entry else None,
        "earlier_versions": entry.get("revisions", []) if entry else [],
        "days": rows,
        "totals": totals(rows, fields),
    }


def cmd_view(args):
    today = current_day(args)
    profile = load("profile.json", {})
    fields = fields_of(profile)
    days = load("days.json", {})
    weeks = load("weeks.json", {})
    notes = load("notes.json", [])

    span = max(1, args.days)
    recent = [day_row(days, today - timedelta(days=i), today) for i in range(span - 1, -1, -1)]
    usual = {}
    for field in fields:
        if field["type"] not in ("number", "scale"):
            continue
        numbers = [row["values"][field["key"]] for row in recent if row.get("values") and field["key"] in row["values"]]
        if len(numbers) >= 3:
            usual[field["key"]] = {"median": statistics.median(numbers), "days_counted": len(numbers)}

    monday = today - timedelta(days=today.weekday())
    closed = [note for note in notes if note.get("status") == "closed"]
    return {
        "today": str(today),
        "weekday": WEEKDAYS[today.weekday()],
        "profile": profile,
        "this_week": week_block(monday, days, weeks, fields, today),
        "last_week": week_block(monday - timedelta(days=7), days, weeks, fields, today),
        "recent_days": recent,
        # Below 3 days of data there is no "usual" yet, so the key is simply absent.
        "usual": usual,
        "open_notes": [note for note in notes if note.get("status") == "open"],
        "recently_closed_notes": closed[-5:],
    }


def cmd_status(args):
    today = current_day(args)
    profile = load("profile.json", {})
    days = load("days.json", {})
    weeks = load("weeks.json", {})
    onboarding = profile.get("onboarding") or {}
    checked = sorted(day for day, entry in days.items() if entry.get("values"))
    marker = HOME / ".owl-version"
    has_plan = week_id(today) in weeks
    if not onboarding.get("done"):
        mode = "setup"
    elif not has_plan:
        mode = "weekly"
    else:
        mode = "daily"
    return {
        "version": marker.read_text(encoding="utf-8").strip() if marker.exists() else None,
        "today": str(today),
        "weekday": WEEKDAYS[today.weekday()],
        "week": week_id(today),
        "suggested_mode": mode,
        "setup_done": bool(onboarding.get("done")),
        "setup_next_step": onboarding.get("next"),
        "has_intake_notes": (DATA / "intake.md").exists(),
        "has_plan_this_week": has_plan,
        "checked_in_today": str(today) in checked,
        "last_checkin": checked[-1] if checked else None,
        "name": profile.get("name"),
        "language": profile.get("language"),
    }


# ---------- notes ----------

def cmd_note_add(args):
    incoming = read_input()
    kind, text = incoming.get("kind"), str(incoming.get("text") or "").strip()
    if kind not in NOTE_KINDS:
        raise OwlError("a note needs 'kind', one of: %s." % ", ".join(NOTE_KINDS))
    if not text:
        raise OwlError("a note needs 'text'.")
    notes = load("notes.json", [])
    note = {
        "id": max([note["id"] for note in notes] or [0]) + 1,
        "kind": kind,
        "text": text,
        "date": str(current_day(args)),
        "status": "open",
    }
    notes.append(note)
    save("notes.json", notes)
    return {"saved": note}


def cmd_note_close(args):
    incoming = read_input()
    notes = load("notes.json", [])
    for note in notes:
        if note["id"] == incoming.get("id"):
            note["status"] = "closed"
            note["outcome"] = str(incoming.get("outcome") or "").strip()
            note["closed"] = str(current_day(args))
            save("notes.json", notes)
            return {"saved": note}
    raise OwlError("there is no note with id %s." % incoming.get("id"))


COMMANDS = {
    "status": cmd_status,
    "profile": cmd_profile,
    "profile-set": cmd_profile_set,
    "week": cmd_week,
    "week-set": cmd_week_set,
    "checkin": cmd_checkin,
    "view": cmd_view,
    "note-add": cmd_note_add,
    "note-close": cmd_note_close,
}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="owl.py", description="Owl's storage. See the top of this file.")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--today", help="pretend today is this date (YYYY-MM-DD)")
    parser.add_argument("--week", help="a week such as 2026-W46 (week, week-set)")
    parser.add_argument("--replace", action="store_true", help="week-set: discard the current plan instead of merging")
    parser.add_argument("--days", type=int, default=14, help="view: how many recent days to include")
    args = parser.parse_args(argv)
    try:
        result = COMMANDS[args.command](args)
    except OwlError as problem:
        sys.stderr.write("Owl storage: %s\n" % problem)
        return 1
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
