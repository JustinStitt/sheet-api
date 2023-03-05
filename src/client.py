import os

from dotenv import load_dotenv
import pygsheets as ps

load_dotenv()


class Client:
    def __init__(self, creds="creds.json", url_env_path="SHEET_URL"):
        self.client = ps.authorize(service_file=creds)
        self.sheet: ps.Spreadsheet = self.client.open_by_url(os.getenv(url_env_path))
        self.sheets: dict[str, ps.Worksheet] = {
            "scoreboard": self.sheet.sheet1,
            "log": self.sheet.worksheet_by_title("log"),
        }
        self.scoreboard: ps.Worksheet = self.sheets["scoreboard"]
        self.log: ps.Worksheet = self.sheets["log"]
