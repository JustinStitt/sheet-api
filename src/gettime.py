from datetime import datetime
import pytz


def gettime():
    pst_time = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("US/Pacific")
    )
    time = str(pst_time)
    time = time[0 : time.index(".")]
    return time
