from datetime import datetime
from collections import defaultdict

from pandas import DataFrame


class Graph:
    def __init__(self, data):
        self.data = data

    def _cleanArg(self, arg: str):
        """strips before equal sign"""
        return arg[arg.index("=") + 1 :]

    def parse(self) -> dict:
        assert type(self.data) is DataFrame, "Graph data is of wrong type"
        self.data = self.data.to_dict()
        # keys = self.data.keys()
        times, actions = list(self.data["A"].values()), list(self.data["B"].values())
        print(f"{times=}, {actions=}")
        assert len(times) == len(
            actions
        ), "mismatched lengths for times, actions. can't construct graph"
        args = [self.data[k] for k in "CDEFG"]

        xs = defaultdict(lambda: list())
        ys = defaultdict(lambda: list())
        teams = []
        for idx, (_time, action) in enumerate(zip(times, actions)):
            if "adjustScore" not in action:
                continue
            # time = datetime.strptime(_time, "%Y-%m-%d %H:%M:%S") # to datetime obj
            team = self._cleanArg(args[1][idx])
            score_delta = self._cleanArg(args[4][idx])
            xs[team].append(_time)
            ys[team].append(score_delta)
            teams.append(team)
        return {"xs": xs, "ys": ys, "teams": teams}
