from datetime import timedelta
from os import getenv
import time
from typing import Literal

from flask_cors import CORS

from dotenv import load_dotenv
from flask import Flask, current_app, jsonify, make_response, request, g as app_ctx
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_restful import Api, Resource
from sheet import Sheet
import logging

load_dotenv()

logging.basicConfig(filename="flask.log", level=logging.DEBUG)
app = Flask(__name__, static_folder="../docs")
api = Api(app)
sheet = Sheet()
CORS(
    app, resources={r"*": {"origins": "*"}}
)  # might need supports_credentials for set-cookie

app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=10**4)
jwt = JWTManager(app)


@app.before_request
def logging_before():
    # Store the start time for the request
    app_ctx.start_time = time.perf_counter()


@app.after_request
def logging_after(response):
    # Get total time in milliseconds
    total_time = time.perf_counter() - app_ctx.start_time
    time_in_ms = int(total_time * 1000)
    # Log the time taken for the endpoint
    current_app.logger.info(
        "%s ms %s %s %s", time_in_ms, request.method, request.path, dict(request.args)
    )
    return response


class Home(Resource):
    """
    Serves the "/" endpoint with method(s): [GET]

    Returns a basic greeting message

    """

    def get(self):
        return "Welcome to the ACM March Madness Sheet API!", 200


class Login(Resource):
    def post(self):
        args = request.args
        username = args["username"]
        password = args["password"]
        if username != getenv("ROOT_USERNAME") or password != getenv("ROOT_PASSWORD"):
            return "bad creds", 401  # unauth

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)


class Docs(Resource):
    def get(self):
        return current_app.send_static_file("app.html")


class CreateTeam(Resource):
    """
    Serves the "/create_team" endpoint with method(s): [GET]

    Creates a new team for the ACM March Madness Event. Adds to Google Sheet backend.

    Teams must be unique and should be chosen with cAsE in mind, as this matters throughout the API.

    URL Parameters:
        - team_name: str
            - The name of the team you want to create.

    Response:
        - 200 -> Team Created Successfully

        - 304 -> Team Already Exists

    """

    def get(self):
        args = request.args
        team_name = args["team_name"]
        captain_name = args["captain_name"]
        resp = sheet.createTeam(team_name, captain_name)
        if resp["status"] == 200:
            res = make_response(jsonify(resp), 200)
            res.set_cookie("team", resp["team_name"])
            return res
        return make_response(jsonify(resp), int(resp["status"]))


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

    @jwt_required()
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

    @jwt_required()
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

    @jwt_required()
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

    @jwt_required()
    def post(self):
        # FIX: won't make a new token on name change (don't use this endpoint for now)
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


class GetTeamFromToken(Resource):
    """
    Serves the "/token_lookup" endpoint with method(s): [GET]

    Finds the team associated with a given `token`.

    Usage: https://<base-url>/token_lookup?token=`token`

    Response:
        - 200 -> {team: <team-matching-specific-token>}

        - 404 -> "Couldn't find team from `token`"

        - Else -> Something Went Wrong
    """

    def get(self):
        args = request.args
        token = args["token"]
        resp = sheet.getTeamFromToken(token)
        if resp is None:  # didn't find team
            return "Couldn't find team from token", 404
        hresp = make_response({"team": resp}, 200)
        hresp.set_cookie("team", resp)
        return hresp


class GetGraphData(Resource):
    """
    Serves the "/get_graph" endpoint with method(s): [GET]

    Return some graph data. Only checks ('adjust_score') method for plotting.

    Response:
        - 200 -> Some graph data
            - {xs: {`team_name0`: [`times`], }, ys: {`team_name0`: [`scores`]}, teams: [`teams`]}

        - Else -> Something Went Wrong
    """

    def get(self):
        resp = sheet.getGraph()
        return resp, 200


class GetInputIndex(Resource):
    def get(self):
        args = request.args
        team_name = args["team_name"]
        resp = sheet.getRandomInputIndexForTeam(team_name=team_name, num_inputs=100)
        return {"index": resp}, 200


class GetJudgement(Resource):
    def get(self):
        args = request.args
        problem = args["problem"]
        # input_idx = int(args["input_index"])
        team_name = args["team_name"]
        input_idx = sheet.getRandomInputIndexForTeam(100, team_name)
        if input_idx not in range(0, 100):
            return {"message": "bad input index"}, 403
        output = args["output"]
        resp = sheet.getJudgement(problem, input_idx, output, team_name)
        return {"judgement": str(resp)}, 200


class GetPastSubmissions(Resource):
    def get(self):
        args = request.args
        team_name = args["team_name"]
        problem = args["problem"]
        resp = sheet.getPastSubmissions(team_name, problem)
        return {"data": resp}, 200


class JoinTeam(Resource):
    def get(self):
        args = request.args
        token = args["token"]
        member_name = args["member_name"]
        resp = sheet.joinTeam(token, member_name)
        if resp is None:
            return {
                "team": None,
                "message": "bad team join, maybe member name empty!",
            }, 403
        hresp = make_response({"team": resp}, 200)
        return hresp


class LeaveTeam(Resource):
    def get(self):
        args = request.args
        team_name = args["team_name"]
        member_name = args["member_name"]
        token = args["token"]
        resp = sheet.leaveTeam(team_name, member_name, token)
        if resp:
            return {"message": "Team Leave successful"}, 200
        return {"message": "Team leave failed"}, 403


api.add_resource(Home, "/")
api.add_resource(Login, "/login")
api.add_resource(Docs, "/docs")
api.add_resource(CreateTeam, "/create_team")
api.add_resource(CreateEvent, "/create_event")
api.add_resource(GetScores, "/scores/<team_name>")
api.add_resource(GetScore, "/scores/<team_name>/<event_name>")
api.add_resource(SetScore, "/set_score")
api.add_resource(AdjustScore, "/adjust_score")
api.add_resource(ChangeTeamName, "/change_team_name")
api.add_resource(GetScoreboard, "/scoreboard")
api.add_resource(GetTeamFromToken, "/token_lookup")
api.add_resource(GetGraphData, "/get_graph")
api.add_resource(GetInputIndex, "/get_index")
api.add_resource(GetJudgement, "/get_judgement")
api.add_resource(GetPastSubmissions, "/get_submissions")
api.add_resource(JoinTeam, "/join_team")
api.add_resource(LeaveTeam, "/leave_team")


if __name__ == "__main__":
    app.run(debug=True)
