from flask import Flask, request
from flask_restful import Api, Resource
from sheet import Sheet
from typing import Literal

app = Flask(__name__)
api = Api(app)
sheet = Sheet()


class Home(Resource):
    """
    Serves the "/" endpoint with method(s): [GET]

    Returns a basic greeting message

    """

    def get(self):
        return "Welcome to the ACM March Madness Sheet API", 200


class CreateTeam(Resource):
    """
    Serves the "/create_team" endpoint with method(s): [POST]

    Creates a new team for the ACM March Madness Event. Adds to Google Sheet backend.

    Teams must be unique and should be chosen with cAsE in mind, as this matters throughout the API.

    URL Parameters:
        - team_name: str
            - The name of the team you want to create.

    Response:
        - 200 -> Team Created Successfully

        - 304 -> Team Already Exists

    """

    def post(self):
        args = request.args
        team_name = args["team_name"]
        resp = sheet.createTeam(team_name)
        return resp


class CreateEvent(Resource):
    """
    Serves the "/create_event" endpoint with method(s): [POST]

    Creates an event for the ACM March Madness Event.

    An event is a competition wherein teams can receive points.

    URL Parameters:
        - event_name: str
            - The name of the event you want to create.

    Response:
        - 200 -> Event Successfully Created

        - Else -> Not Created

    """

    def post(self):
        args = request.args
        event_name = args["event_name"]
        resp = sheet.createEvent(event_name)
        return resp


class GetScores(Resource):
    """
    Serves the "/scores/team_name" endpoint with method(s): [GET]

    Returns the scores for a specific team (case-sensitive).

    Example output: `"Flying Felines:{'AOC-0': 0, 'AOC-1': 0, 'AOC-2': 0, 'AOC-3': 0, 'AOC-4': 944, 'HACKATHON': 0, 'Some New Event': 0}"`

    Response:
        - scores, 200 -> one score per event

        - Else -> Something Went Wrong

    """

    def get(self, team_name):
        scores, events_to_idx = sheet.getScores(team_name)
        resp = {
            event: score for event, score in zip(events_to_idx.keys(), list(scores))
        }
        # scores = [score for score in sheet.getScores(team_name)[0]]
        return f"{team_name}:{resp}", 200


class GetScore(Resource):
    """
    Serves the "/scores/team_name/event_name" endpoint with method(s): [GET]

    Returns the scores for a specific team (case-sensitive) and specific event (case-sensitive).

    Response:
        - score, 200 -> one score

        - Else -> Something Went Wrong

    """

    def get(self, team_name, event_name):
        score = sheet.getScore(team_name, event_name)
        return str(score), 200


class SetScore(Resource):
    """
    Serves the "/set_score" endpoint with method(s): [POST]

    Sets the current score for a team for a specific event.

    URL Parameters:
        - team_name: str
            - The name of the team (case-sensitive).

        - event_name: str
            - The name of the event (case-sensitive).

    Response:
        - 200 -> Score Successfully Set

        - Else -> Something Went Wrong

    """

    def post(self):
        args = request.args
        team_name = args["team_name"]
        event_name = args["event_name"]
        score = args["score"]
        resp = sheet.setScore(event_name, team_name, int(score))
        return resp


class AdjustScore(Resource):
    """
    Serves the "/adjust_score" endpoint with method(s): [POST]

    Adjusts the current score for a specific team in a specific event.

    URL Parameters:
        - team_name: str
            - The name of the team (case-sensitive).

        - event_name: str
            - The name of the event (case-sensitive).

        - delta: int
            - The amount to change the score by (whole number, pls <3).

    Response:
        - 200 -> Score Successfully Adjusted

        - Else -> Something Went Wrong

    """

    def post(self):
        args = request.args
        team_name = args["team_name"]
        event_name = args["event_name"]
        delta = args["delta"]
        resp = sheet.adjustScore(event_name, team_name, int(delta))
        return resp


class ChangeTeamName(Resource):
    """
    Serves the "/change_team_name" endpoint with method(s): [POST]
    Sets the current score for a team for a specific event.

    URL Parameters:
        - team_name: str
            - The name of the team you want to change (case-sensitive).

        - new_name: str
            - The new name for the team.
    Response:
        - 200 -> Team Name Successfully Changed

        - Else -> Something Went Wrong
    """

    def post(self):
        args = request.args
        team_name = args["team_name"]
        new_name = args["new_name"]
        resp = sheet.changeTeamName(team_name, new_name)
        return resp


class GetScoreboard(Resource):
    """
    Serves the "/scoreboard" endpoint with method(s): [GET]

    Sets the current score for a team for a specific event.

    Response:
        - scoreboard -> Just look at it, it's a mess, but it's a scoreboard.
            - Here's an example of the output v.s the actual sheet (https://prnt.sc/6EJa_TqCoO8f)

        - Else -> Something Went Wrong
    """

    def get(self):
        scoreboard = sheet.getScoreboard()
        assert type(scoreboard) is not Literal[False]
        return scoreboard.to_json(orient="records")


api.add_resource(Home, "/")
api.add_resource(CreateTeam, "/create_team")
api.add_resource(CreateEvent, "/create_event")
api.add_resource(GetScores, "/scores/<team_name>")
api.add_resource(GetScore, "/scores/<team_name>/<event_name>")
api.add_resource(SetScore, "/set_score")
api.add_resource(AdjustScore, "/adjust_score")
api.add_resource(ChangeTeamName, "/change_team_name")
api.add_resource(GetScoreboard, "/scoreboard")

if __name__ == "__main__":
    app.run(debug=True)
