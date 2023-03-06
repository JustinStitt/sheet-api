from flask import Flask, request
from flask_restful import Api, Resource
from sheet import Sheet
from typing import Literal

app = Flask(__name__)
api = Api(app)
sheet = Sheet()


class HelloWorld(Resource):
    def get(self):
        return {"hello": "world"}


class CreateTeam(Resource):
    def post(self):
        args = request.args
        team_name = args["team_name"]
        resp = sheet.createTeam(team_name)
        return resp


class CreateEvent(Resource):
    def post(self):
        args = request.args
        event_name = args["event_name"]
        resp = sheet.createEvent(event_name)
        return resp


class GetScores(Resource):
    def get(self, team_name):
        scores, events_to_idx = sheet.getScores(team_name)
        resp = {
            event: score for event, score in zip(events_to_idx.keys(), list(scores))
        }
        # scores = [score for score in sheet.getScores(team_name)[0]]
        return f"{team_name}:{resp}", 200


class GetScore(Resource):
    def get(self, team_name, event_name):
        score = sheet.getScore(team_name, event_name)
        return str(score), 200


class SetScore(Resource):
    def post(self):
        args = request.args
        team_name = args["team_name"]
        event_name = args["event_name"]
        score = args["score"]
        resp = sheet.setScore(event_name, team_name, int(score))
        return resp


class AdjustScore(Resource):
    def post(self):
        args = request.args
        team_name = args["team_name"]
        event_name = args["event_name"]
        delta = args["delta"]
        resp = sheet.adjustScore(event_name, team_name, int(delta))
        return resp


class ChangeTeamName(Resource):
    def post(self):
        args = request.args
        team_name = args["team_name"]
        new_name = args["new_name"]
        resp = sheet.changeTeamName(team_name, new_name)
        return resp


class GetScoreboard(Resource):
    def get(self):
        scoreboard = sheet.getScoreboard()
        assert type(scoreboard) is not Literal[False]
        return scoreboard.to_json(orient="records")


api.add_resource(HelloWorld, "/")
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
