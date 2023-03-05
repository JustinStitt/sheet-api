from typing import Literal
import pygsheets as ps
import pandas as pd
from dotenv import load_dotenv
from client import Client
from logger import Logger
import inspect

load_dotenv()


class Sheet:
    def __init__(self, client: Client, logger: Logger):
        self._client = client
        self._logger = logger
        # if logger and client.client != logger._client:
        #     raise Exception("Client and Logger not synced.")
        self.scoreboard = self._client.scoreboard

    def getScoreboard(self) -> pd.DataFrame | Literal[False]:
        return self.scoreboard.get_as_df()

    # TODO: reduce redundancy in _findEvent and _findTeam
    def _findEvent(self, event_name: str) -> ps.Cell:
        cells = self.scoreboard.find(event_name)
        if len(cells) == 0:
            raise ps.CellNotFound(
                f"Could not find event: {event_name}. Check spelling (case sensitive)."
            )
        return cells[0]

    def _findTeam(self, team_name: str) -> ps.Cell:
        cells = self.scoreboard.find(team_name)
        if len(cells) == 0:
            raise ps.CellNotFound(
                f"Could not find team: {team_name}. Check spelling (case sensitive)."
            )
        return cells[0]

    def changeTeamName(self, old_team_name: str, new_team_name: str):
        old_team_cell: ps.Cell = self._findTeam(old_team_name)
        old_team_cell.set_value(new_team_name)
        old_team_cell.link(self.scoreboard, update=True)
        self._logger.log()

    def _getNumberOfTeams(self) -> int:
        header_row = self.scoreboard.get_row(1, include_tailing_empty=False)
        return len(header_row) - 1

    def _getNumberOfEvents(self) -> int:
        leading_col = self.scoreboard.get_col(1, include_tailing_empty=False)
        return len(leading_col) - 1

    def createTeam(self, team_name: str):
        try:
            self._findTeam(team_name)
        except:
            idx = self._getNumberOfTeams() + 1
            zero_pad = [0 for _ in range(self._getNumberOfEvents())]
            self.scoreboard.insert_cols(idx, values=[team_name, *zero_pad])
            self._logger.log()
        else:
            print(f'Team: "{team_name}" already exists!')

    def createEvent(self, event_name: str):
        idx = self._getNumberOfEvents() + 1
        zero_pad = [0 for _ in range(self._getNumberOfTeams())]
        self.scoreboard.insert_rows(idx, values=[event_name, *zero_pad])
        self._logger.log()

    def _getEventTeamCell(self, event_name: str, team_name: str) -> str | None:
        try:
            team_cell = self._findTeam(team_name)
            event_cell = self._findEvent(event_name)
        except:
            print(
                "Couldn't find team or event in _getEventTeamCell",
                event_name,
                team_name,
            )
        else:
            # !! probably breaks when over 26 teams due to 'AA' label
            return team_cell.label[0] + event_cell.label[1:]

        return None

    def getScores(self, team_name: str) -> tuple[dict[int, int], dict[str, int]]:
        sb: pd.DataFrame = self.getScoreboard()  # type: ignore
        events = dict(sb["-"])
        event_to_idx = {k: v for (v, k) in events.items()}
        return sb[team_name], event_to_idx

    def setScore(self, event_name: str, team_name: str, score: int):
        label = self._getEventTeamCell(event_name, team_name)
        self.scoreboard.update_value(label, str(score))
        self._logger.log()

    def adjustScore(self, event_name: str, team_name: str, score_delta: int):
        assert type(score_delta) is int, "Score Delta must be an integer!"
        label = self._getEventTeamCell(event_name, team_name)
        team_col, event_to_idx = self.getScores(team_name)
        score_idx = event_to_idx[event_name]
        current_score = team_col[score_idx]
        self.scoreboard.update_value(label, str(current_score + score_delta))
        self._logger.log(old_score=current_score, new_score=current_score + score_delta)


if __name__ == "__main__":
    gc = Client()
    logger = Logger(gc)
    sheet = Sheet(gc, logger)
    # sheet.setScore("HACKATHON", "Team Three", 99)
    # scores = sheet.getScores("Team Three")
    sheet.adjustScore("HACKATHON", "Team Three", 18)
    # sheet.createTeam("Team Five")
    # sheet.createEvent("Cool Event")
    # sheet.changeTeamName("Flying Felines", "V2 Coolio Team")
    # sheet._findTeam("Soprano Gang")
    # sheet.addTeam("Some New Team")
    # print(sheet.getScoreboard())


# use scoreboard.unlink() and scoreboard.link() to batch api calls
