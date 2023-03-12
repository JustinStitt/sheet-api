from hashlib import new
import json
from os import getenv
from typing import Literal
import time

from dotenv import load_dotenv
import pandas as pd
import pygsheets as ps

from client import Client
from logger import Logger
from graph import Graph
from sanitize import sanitize

load_dotenv()


class Sheet:
    kSCOREBOARD_DELAY = 10  # how often to refetch scoreboard data

    def __init__(self):
        self._client = Client()
        self._logger = Logger(self._client)
        self._scoreboard = self._client.scoreboard
        self._tokens = self._client.tokens
        self.last_scoreboard_fetch_time = time.time()
        self.last_scoreboard_fetch_data: pd.DataFrame | Literal[False] = False

    def getScoreboard(self) -> pd.DataFrame | Literal[False]:
        current_time = time.time()
        if (
            current_time - self.last_scoreboard_fetch_time < Sheet.kSCOREBOARD_DELAY
            and type(self.last_scoreboard_fetch_data) is pd.DataFrame
        ):
            # cheap work
            print("cheap")
            return self.last_scoreboard_fetch_data

        # expensive work
        print("expensive")
        self.last_scoreboard_fetch_time = current_time
        scoreboard_data = self._scoreboard.get_as_df()
        self.last_scoreboard_fetch_data = scoreboard_data
        return scoreboard_data

    @sanitize
    def _findEvent(self, event_name: str) -> ps.Cell:
        cells = list(
            filter(
                lambda c: c.value == event_name,
                self._scoreboard.get_col(
                    1, returnas="cell", include_tailing_empty=False
                ),
            )
        )

        if len(cells) == 0:
            raise ps.CellNotFound(
                f"Could not find event: {event_name}. Check spelling (case sensitive)."
            )
        return cells[0]

    @sanitize
    def _findTeam(self, team_name: str) -> ps.Cell:
        cells = list(
            filter(
                lambda c: c.value == team_name,
                self._scoreboard.get_row(
                    1, returnas="cell", include_tailing_empty=False
                ),
            )
        )
        if len(cells) == 0:
            raise ps.CellNotFound(
                f"Could not find team: {team_name}. Check spelling (case sensitive)."
            )
        return cells[0]

    @sanitize
    def changeTeamName(self, old_team_name: str, new_team_name: str):
        old_team_cell: ps.Cell = self._findTeam(old_team_name)
        old_team_cell.set_value(new_team_name)
        old_team_cell.link(self._scoreboard, update=True)
        self._logger.log()
        return f'Successfully changed team: "{old_team_name}" to "{new_team_name}"', 200

    def _getNumberOfTeams(self) -> int:
        header_row = self._scoreboard.get_row(1, include_tailing_empty=False)
        return len(header_row) - 1

    def _getNumberOfEvents(self) -> int:
        leading_col = self._scoreboard.get_col(1, include_tailing_empty=False)
        return len(leading_col) - 1

    @sanitize
    def createTeam(self, team_name: str):
        if len(team_name) < 1:
            return {
                "message": "invalid team name",
                "token": "",
                "team_name": team_name,
                "status": 404,
            }
        try:
            self._findTeam(team_name)
        except:
            idx = self._getNumberOfTeams() + 1
            zero_pad = [0 for _ in range(self._getNumberOfEvents())]
            token = self._generateToken(team_name)
            self._scoreboard.insert_cols(idx, values=[team_name, *zero_pad])
            self._tokens.insert_rows(idx, values=[team_name, token])
            self._logger.log(token=token)
            return {
                "message": f"Team {team_name} created successfully",
                "token": token,
                "team_name": team_name,
                "status": 200,
            }
        return {
            "message": f'Team: "{team_name}" already exists!',
            "token": "",
            "team_name": team_name,
            "status": 304,
        }

    @sanitize
    def createEvent(self, event_name: str):
        idx = self._getNumberOfEvents() + 1
        zero_pad = [0 for _ in range(self._getNumberOfTeams())]
        self._scoreboard.insert_rows(idx, values=[event_name, *zero_pad])
        self._logger.log()
        return f'Event: "{event_name}" created', 200

    @sanitize
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

    @sanitize
    def getScores(self, team_name: str) -> tuple[dict[int, int], dict[str, int]]:
        sb = self.getScoreboard()
        assert type(sb) is pd.DataFrame

        events = dict(sb["-"])
        event_to_idx = {k: v for (v, k) in events.items()}
        return sb[team_name], event_to_idx

    @sanitize
    def getScore(self, team_name: str, event_name: str) -> int:
        team_col, event_to_idx = self.getScores(team_name)
        score_idx = event_to_idx[event_name]
        score = team_col[score_idx]
        return score

    @sanitize
    def setScore(self, event_name: str, team_name: str, score: int):
        label = self._getEventTeamCell(event_name, team_name)
        self._scoreboard.update_value(label, str(score))
        self._logger.log()
        return "success", 200

    @sanitize
    def adjustScore(self, event_name: str, team_name: str, score_delta: int):
        assert type(score_delta) is int, "Score Delta must be an integer!"
        label = self._getEventTeamCell(event_name, team_name)
        current_score = self.getScore(team_name, event_name)
        self._scoreboard.update_value(label, str(current_score + score_delta))
        self._logger.log(old_score=current_score, new_score=current_score + score_delta)
        return "success", 200

    @sanitize
    def getTeamFromToken(self, token: str):
        tokens_to_teams: dict[str, str] = self._getTokensToTeams()
        assert type(token) is str and len(
            token
        ), "Bad Token Type, must be non-empty str"

        return tokens_to_teams.get(token, None)

    def _getTokens(self):
        """
        Retrieve the current list of tokens so we can ensure no
        duplicate token is made
        """
        tokens = self._tokens.get_col(2, include_tailing_empty=False)
        return tokens

    def _getTokensToTeams(self) -> dict[str, str]:
        df = self._tokens.get_as_df()
        assert type(df) is not Literal[False], "Bad dataframe on token fetch"

        tt = df.to_dict()
        token_to_teams = {
            tt["Token"][i]: tt["Team Name"][i] for i in range(len(tt["Token"].keys()))
        }
        return token_to_teams

    @sanitize  # HACK: probably don't need to sanitize here
    def _generateToken(self, team_name: str):
        """
        Generate a unique token based on a hash of the team name
        """
        from hashlib import sha1

        team_name = team_name.replace(" ", "").lower()

        current_tokens = self._getTokens()
        adjectives = open("../assets/adjectives.txt", "r").readlines()
        nouns = open("../assets/nouns.txt", "r").readlines()

        adjective_hash = sha1(team_name.encode()).hexdigest()
        adjective_index = int(adjective_hash, 16) % len(adjectives)

        noun_hash = sha1(team_name.encode()).hexdigest()
        noun_index = int(noun_hash, 16) % len(nouns)

        token = (
            f"{adjectives[adjective_index].strip()}{nouns[noun_index].strip()}".lower()
        )
        if token in current_tokens:
            return self._generateToken(team_name + getenv("SECRET_HASH_APPEND"))  # type: ignore

        return token

    def getGraph(self):
        log = self._logger.getLog()
        graph = Graph(log)
        return graph.parse()


if __name__ == "__main__":
    sheet = Sheet()
    sheet._generateGraph()
    # sheet.setScore("HACKATHON", "Team Three", 99)
    # scores = sheet.getScores("Team Three")
    # sheet.adjustScore("AOC-4", "Team Four", 6)
    # sheet.createTeam("Team Five")
    # sheet.createEvent("Cool Event")
    # sheet.changeTeamName("Flying Felines", "V2 Coolio Team")
    # sheet._findTeam("Soprano Gang")
    # sheet.addTeam("Some New Team")
    # print(sheet.getScoreboard())
    # use scoreboard.unlink() and scoreboard.link() to batch api calls
