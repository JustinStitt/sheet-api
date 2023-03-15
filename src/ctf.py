import logging
import re
from pygsheets import Worksheet


# TODO: check prior solve of CTF chall before awarding points
class CTF:
    category_to_index = {
        "web": 0,
        "rev": 1,
        "forensics": 2,
        "osint": 3,
        "crypto": 4,
        "linux": 5,
    }  # WARNING: use same lookup table for hasPriorSolve-equiv

    def __init__(self, ctf: Worksheet):
        self.ctf: Worksheet = ctf

    def isFlagCorrect(self, category: str, problem_idx: int, flag: str) -> bool:
        flag = re.sub(r"[^a-zA-Z{}_]", "", flag)
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

        actual_flag = problems[problem_idx]
        return flag == actual_flag
