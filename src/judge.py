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
        # problem is of form "1a" or "1b" or "4a"
        problem_number = int(re.findall(r"\d+", problem)[0])
        problem_part = re.findall(r"[a-z]{1}", problem)[0]
        relevant_sheet = self.problems[problem_number - 1]

        cidx = ord(problem_part) - ord("a") + 1
        relevant_col = relevant_sheet.get_col(cidx, include_tailing_empty=False)
        correct_output = relevant_col[input_idx + 1]
        result = correct_output == output
        row = [gettime(), team_name, problem, str(result)]
        self.submissions.append_table(row, overwrite=True)  # type: ignore
        return result

    def getPastSubmissions(self, team_name: str, problem: str):
        return self.submissions.get_as_df()
