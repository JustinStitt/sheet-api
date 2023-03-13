import os

from dotenv import load_dotenv
import pygsheets as ps

load_dotenv()


class Client:
    def __init__(self, creds="creds.json", url_env_path="SHEET_URL"):
        self.client = ps.authorize(service_file=creds)
        self.sheet: ps.Spreadsheet = self.client.open_by_url(os.getenv(url_env_path))
        self.sheets: dict[str, ps.Worksheet | list[ps.Worksheet]] = {
            "scoreboard": self.sheet.sheet1,
            "log": self.sheet.worksheet_by_title("log"),
            "tokens": self.sheet.worksheet_by_title("tokens"),
            "problems": [
                self.sheet.worksheet_by_title("p" + str(p)) for p in range(1, 6)
            ],
        }
        self.scoreboard: ps.Worksheet | list[ps.Worksheet] = self.sheets["scoreboard"]
        self.tokens: ps.Worksheet | list[ps.Worksheet] = self.sheets["tokens"]
        self.log: ps.Worksheet | list[ps.Worksheet] = self.sheets["log"]
        self.problems: ps.Worksheet | list[ps.Worksheet] = self.sheets["problems"]
