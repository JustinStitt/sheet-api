import logging
import re
from pygsheets import Worksheet
from gettime import gettime


# TODO: check prior solve of CTF chall before awarding points
class CTF:
    category_to_index = {
        "web": 0,
        "rev": 1,
        "forensics": 2,
        "networking": 3,
        "crypto": 4,
        "linux": 5,
    }  # WARNING: use same lookup table for hasPriorSolve-equiv

    def __init__(self, ctf: Worksheet, submissions: Worksheet):
        self.ctf: Worksheet = ctf
        self.submissions: Worksheet = submissions

    def isFlagCorrect(
        self, category: str, problem_idx: int, flag: str, team_name: str
    ) -> bool:
        flag = re.sub(r"[^a-zA-Z{}_0-9]", "", flag)
        category_index = CTF.category_to_index.get(category, None)
        if category_index is None or not len(flag) or problem_idx < 0:
            logging.info(
                f"Bad category or problem index {category=}, {category_index=}, {problem_idx=}"
            )
            return False  # bad flag

        problems = self.ctf.get_col(category_index + 1, include_tailing_empty=False)[1:]
        print(problems, problem_idx)
        if problem_idx > len(problems) - 1:
            logging.info(
                f"Bad problem index for isFlagCorrect {category=}, {category_index=}, {problem_idx=}, {problems=}"
            )
            return False  # bad problem index
        problem = f"{category}-{problem_idx}"
        actual_flag = problems[problem_idx]
        result = flag == actual_flag
        row = [gettime(), team_name, problem, str(result), str(0), flag]
        self.submissions.append_table(row, overwrite=True)  # type: ignore
        return result

    def getSolvedFlags(self, team_name: str, category: str):
        # iterate through submissions
        solved_idxs = []
        records = self.submissions.get_all_records()
        for record in records:
            team = record["team-name"]
            problem = record["problem"]
            result = record["result"]
            if category not in problem or "-" not in problem:
                continue  # not the right problem! (ctf category)
            num = int(problem[problem.index("-") + 1 :])

            if team == team_name and result == "TRUE":
                solved_idxs.append(num)

        return solved_idxs
