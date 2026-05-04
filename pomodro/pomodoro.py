import time
import sys
import json
import datetime

# --- Settings ---
WORK_MINUTES        = 1
SHORT_BREAK_MINUTES = 1
LONG_BREAK_MINUTES  = 15
CYCLES_BEFORE_LONG  = 4   # how many work sessions before a long break

LOG_FILE = "pomodoro_log.json"   # the file where sessions are saved


# --- Logging functions ---

def load_log():
    """Read the log file and return its contents as a Python list.
    If the file doesn't exist yet, return an empty list instead."""
    try:
        with open(LOG_FILE, "r") as f:   # open for reading
            return json.load(f)          # parse JSON text → Python list
    except FileNotFoundError:
        return []                        # first time running: no file yet


def save_log(log):
    """Write the log list back to the file as JSON."""
    with open(LOG_FILE, "w") as f:       # open for writing (overwrites each time)
        json.dump(log, f, indent=2)      # convert Python list → JSON text


def log_session(cycle, start_time, end_time):
    """Append one completed work session to the log file."""
    log = load_log()   # load what's already there

    entry = {
        "date":  start_time.strftime("%Y-%m-%d"),   # e.g. "2026-05-03"
        "cycle": cycle,
        "start": start_time.strftime("%H:%M:%S"),   # e.g. "09:00:00"
        "end":   end_time.strftime("%H:%M:%S"),      # e.g. "09:25:00"
    }

    log.append(entry)   # add new entry to the list
    save_log(log)       # write the updated list back to disk
    print(f"  (Session logged: cycle {cycle} on {entry['date']})")


# --- Timer functions ---

def countdown(seconds):
    """Count down from `seconds` to zero, printing a live clock."""
    while seconds > 0:
        minutes = seconds // 60
        secs    = seconds % 60
        display = f"{minutes:02d}:{secs:02d}"
        print(display, end="\r")
        time.sleep(1)
        seconds -= 1
    print("00:00")


def beep(times=3):
    """Sound the terminal bell `times` times."""
    for _ in range(times):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.4)


def run_session(label, minutes, cycle=None):
    """Print a header, run the countdown, then print a completion message.
    If cycle is provided (work sessions only), log the session."""
    print(f"\n{'='*40}")
    print(f"  {label}  ({minutes} minutes)")
    print(f"{'='*40}")

    start_time = datetime.datetime.now()   # record when the session starts
    countdown(minutes * 60)
    end_time = datetime.datetime.now()     # record when it ends

    beep()
    print(f"\n{'*'*40}")
    print(f"  *** {label} complete! ***")
    print(f"{'*'*40}\n")

    if cycle is not None:                  # only log work sessions, not breaks
        log_session(cycle, start_time, end_time)


def run_pomodoro():
    """Run Pomodoro cycles until the user quits with Ctrl-C."""
    cycle = 0

    print("Pomodoro Timer started. Press Ctrl-C at any time to stop.\n")

    while True:
        cycle += 1
        print(f"\n--- Cycle {cycle} ---")

        run_session("WORK SESSION", WORK_MINUTES, cycle=cycle)   # pass cycle to log it

        if cycle % CYCLES_BEFORE_LONG == 0:
            run_session("LONG BREAK", LONG_BREAK_MINUTES)        # no cycle = not logged
        else:
            run_session("SHORT BREAK", SHORT_BREAK_MINUTES)


# --- Entry point ---
if __name__ == "__main__":
    try:
        run_pomodoro()
    except KeyboardInterrupt:
        print("\n\nTimer stopped. Great work today!")
