import re
import pygsheets as ps


class Judge:
    def __init__(self, problems):
        self.problems = problems

    def getJudgement(self, problem: str, input_idx: int, output: str):
        # problem is of form "1a" or "1b" or "4a"
        problem_number = int(re.findall(r"\d+", problem)[0])
        problem_part = re.findall(r"[a-z]{1}", problem)[0]
        relevant_sheet = self.problems[problem_number - 1]

        cidx = ord(problem_part) - ord("a") + 1
        relevant_col = relevant_sheet.get_col(cidx, include_tailing_empty=False)
        correct_output = relevant_col[input_idx + 1]
        return correct_output == output
