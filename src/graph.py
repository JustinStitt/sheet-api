from datetime import datetime

from pandas import DataFrame


class Graph:
    def __init__(self, data):
        self.data = data

    def parse(self) -> dict[str, list[str]]:
        assert type(self.data) is DataFrame, "Graph data is of wrong type"
        self.data = self.data.to_dict()
        # keys = self.data.keys()
        times, actions = list(self.data["A"].values()), list(self.data["B"].values())
        print(f"{times=}, {actions=}")
        assert len(times) == len(
            actions
        ), "mismatched lengths for times, actions. can't construct graph"
        args = [self.data[k] for k in "CDEFG"]

        xs = []
        ys = []
        teams = []
        for idx, (_time, action) in enumerate(zip(times, actions)):
            if "adjustScore" not in action:
                continue
            # time = datetime.strptime(_time, "%Y-%m-%d %H:%M:%S")
            xs.append(_time)
            ys.append(args[4][idx])
            teams.append(args[1][idx])
        return {"xs": xs, "ys": ys, "teams": teams}
