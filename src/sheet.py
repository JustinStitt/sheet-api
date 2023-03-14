from hashlib import new
import json
from os import getenv
from typing import Literal
from hashlib import sha1
import time
import logging
import re

from dotenv import load_dotenv
import pandas as pd
import pygsheets as ps

from client import Client
from logger import Logger
from judge import Judge
from graph import Graph
from sanitize import sanitize

load_dotenv()
kPOINTS = json.loads(getenv("POINTS"))  # type: ignore


class Sheet:
    kSCOREBOARD_DELAY = 10  # how often to refetch scoreboard data

    def __init__(self):
        self._client = Client()
        self._logger = Logger(self._client)
        self._judge = Judge(self._client.problems, self._client.submissions)
        self._scoreboard = self._client.scoreboard
        self._tokens = self._client.tokens
        self._teams = self._client.teams
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
    def createTeam(self, team_name: str, member_name: str):
        if (
            len(team_name) <= 1
            or len(team_name) > 32
            or len(member_name) <= 1
            or len(member_name) > 32
        ):
            return {
                "message": "Invalid team name length. Length must be greater than 1 and less than 33",
                "token": "",
                "team_name": team_name,
                "status": 403,
            }
        try:
            self._findTeam(team_name)
        except:
            idx = self._getNumberOfTeams() + 1
            zero_pad = [0 for _ in range(self._getNumberOfEvents())]
            token = self._generateToken(team_name)
            self._scoreboard.insert_cols(idx, values=[team_name, *zero_pad])
            self._tokens.insert_rows(idx, values=[team_name, token])
            self._teams.insert_rows(idx, values=[team_name, member_name])
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
    def _getEventTeamCell(
        self, event_name: str, team_name: str
    ) -> tuple[int, int] | None:
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
            # return team_cell.label[0] + event_cell.label[1:]
            return (event_cell.row, team_cell.col)

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
        row, col = self._getEventTeamCell(event_name, team_name)
        logging.debug(f"ADJUSTSCORE: {row=},{col=}")
        current_score = self.getScore(team_name, event_name)
        self._scoreboard.update_value((row, col), str(current_score + score_delta))
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

    def getRandomInputIndexForTeam(self, num_inputs: int, team_name: str) -> int:
        """hash team name and return index from [0, 99]"""
        team_hash = sha1(team_name.encode()).hexdigest()
        return int(team_hash, 16) % num_inputs

    def getJudgement(
        self, problem: str, input_idx: int, output: str, team_name: str
    ) -> bool:
        has_prior_solve = self._judge.hasPriorSolve(team_name, problem)
        judgement = self._judge.getJudgement(problem, input_idx, output, team_name)
        problem_number = problem[
            0
        ]  # HACK: doesn't work for double digit problems like 14c
        logging.info(
            f"christOSS log: {has_prior_solve=}, {judgement=}, {problem_number=}"
        )
        if judgement == True and not has_prior_solve and problem_number in "0123456789":
            event_name = "woc" + str(int(problem_number) - 1)
            try:
                logging.debug(f"TRYING KPOINTS {problem}")
                value = int(kPOINTS[problem])
                print(f"{value=}")
            except:
                logging.debug(f"PROBLEM DOESNT EXIST in kPOINTS {problem=}")
                return False
            print("ADJUSTING SCORE FOR: ", problem, team_name, output)
            logging.info(f"ADJUSTING SCORE: {problem=}, {team_name=}, {output=}")
            try:
                self.adjustScore(event_name, team_name, value)
            except:
                logging.error("COULDNT ADJUST SCORE FOR")
                return False  # couldn't adjust score for some reason
        return judgement

    def getPastSubmissions(self, team_name: str, problem: str):
        return self._judge.getPastSubmissions(team_name, problem)

    @sanitize
    def joinTeam(self, token: str, member_name: str):
        if len(member_name) < 2:
            return None
        records = self._teams.get_all_records()
        print("records: ", records)
        to_join = self.getTeamFromToken(token)
        if to_join is None:
            print("Team not found with token: ", token)
            return None
        for ridx, record in enumerate(records):
            if record["team_name"] == to_join:
                # find first empty team slot
                k = 0
                for i in range(0, 40):
                    k = str(i)
                    if record[k] == "":
                        break

                cell = self._teams.cell((ridx + 2, int(k) + 3))
                cell.set_value(member_name)
                return to_join
        return None

    def leaveTeam(self, team_name: str, member_name: str):
        # do tokens match?
        if len(team_name) < 1 or len(member_name) < 1:
            print("Empty args")
            return False
        # if self.getTeamFromToken(token) != team_name:
        #     print("Cant join team if token doesn't match!")
        #     return False
        records = self._teams.get_all_records()
        for ridx, record in enumerate(records):
            if record["team_name"] == team_name:
                # find our name in it
                k = 0
                for i in range(0, 40):
                    k = str(i)
                    if record[k] == member_name:
                        break
                cell = self._teams.cell((ridx + 2, int(k) + 3))
                # cell.set_value("<vacancy>")
                cell.set_text_format("strikethrough", True)
                return True
        return False


if __name__ == "__main__":
    sheet = Sheet()
    # print(sheet.getPastSubmissions("acmgang", "1a")
    # sheet.adjustScore("woc0", "acmgang", 100)
    # print(sheet.getRandomInputIndexForTeam(100, "mtndew"))
    # # sheet.createTeam("asdfffasd", "kevin")
    # sheet.joinTeam("boredpheasant", "kevin")
    # # index = sheet.getRandomInputIndexForTeam(100, "teamtwoayo")
    # print("index: ", index)
    # print(sheet.getJudgement("1b", index, "861", "teamtwoayo"))
