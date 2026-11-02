from datetime import UTC, date, datetime, timedelta


def Now() :
    return datetime.now()

def NowWithDelta(delta: int) :
    """return the current Datetime after modifying it with delta.

    Delta is the number of minutes"""
    return Now() + timedelta(minutes=delta)