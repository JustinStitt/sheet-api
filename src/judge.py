import re
import pygsheets as ps

from gettime import gettime


class Judge:
    def __init__(self, problems, submissions):
        self.problems = problems
        self.submissions = submissions

    def getJudgement(
        self, problem: str, input_idx: int, output: str, team_name: str
    ) -> bool:
        team_name = re.sub(r"[^a-zA-Z]", "", team_name).lower()
        # problem is of form "1a" or "1b" or "4a"
        problem_number = int(re.findall(r"\d+", problem)[0])
        problem_part = re.findall(r"[a-z]{1}", problem)[0]
        relevant_sheet = self.problems[problem_number - 1]

        cidx = ord(problem_part) - ord("a") + 1
        relevant_col = relevant_sheet.get_col(cidx, include_tailing_empty=False)
        correct_output = relevant_col[input_idx + 1]
        result = correct_output == output
        row = [gettime(), team_name, problem, str(result), str(input_idx), output]
        self.submissions.append_table(row, overwrite=True)  # type: ignore
        return result

    def hasPriorSolve(self, team_name: str, problem: str) -> bool:
        team_name = re.sub(r"[^a-zA-Z]", "", team_name).lower()
        print(f"CHECKING PRIOR SOLVE {team_name=}, {problem=}")
        # print(self.getPastSubmissions(team_name, problem))
        records = self.submissions.get_all_records()
        for record in records:
            if (
                record.get("team-name", None) == team_name
                and record.get("problem", None) == problem
                and record.get("result", None) == "TRUE"
            ):
                print("hit: ", record)
                return True

        return False

    def getPastSubmissions(self, team_name: str, problem: str):
        res = self.submissions.get_as_df().to_dict()
        out = {"time": {}, "result": {}, "problem": {}}
        count = 0
        for i in range(len(res["time"])):
            print(res["team-name"][i], team_name, problem)
            if res["team-name"][i] == team_name and res["problem"][i] == problem:
                out["time"][count] = res["time"][i]
                out["result"][count] = res["result"][i]
                out["problem"][count] = res["problem"][i]
                count += 1
        return out
