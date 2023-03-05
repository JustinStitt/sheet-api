import pytz
import inspect
from datetime import datetime
from client import Client


class Logger:
    def __init__(self, client: Client):
        self._client = client
        self._scoreboard = self._client.scoreboard
        self._log = self._client.log

    def log(self, **kwargs):
        pst_time = pytz.utc.localize(datetime.utcnow()).astimezone(
            pytz.timezone("US/Pacific")
        )

        current_frame = inspect.currentframe()
        assert current_frame is not None

        previous_frame = current_frame.f_back
        assert previous_frame is not None

        args, _, _, values = inspect.getargvalues(previous_frame)

        row = [str(pst_time), previous_frame.f_code.co_name]

        for arg in args:
            if arg == "self":
                continue
            row.append(f"{arg}={values[arg]}")

        for k, v in kwargs.items():  # any additional args
            row.append(f"{k}={v}")

        self._log.append_table(row, overwrite=True)
