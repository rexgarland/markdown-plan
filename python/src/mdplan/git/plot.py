import json
import subprocess
import os
import platform
import tempfile
from importlib_resources import files


from .history import GitHistory


def native_open(file):
    if platform.system() == "Darwin":
        subprocess.call(("open", file))
    elif platform.system() == "Windows":
        os.startfile(file)
    else:
        subprocess.call(("xdg-open", file))


class GitPlot:
    history: GitHistory
    template_path = files("mdplan").joinpath("data").joinpath("plot_template.html")

    def __init__(self, history: GitHistory):
        self.history = history

    def to_html(self) -> str:
        text = self.history.to_json()
        data = json.loads(text)

        def to_total(v):
            return {"date": v["date"], "type": "total", "tasks": v["tasks"]["total"]}

        def to_completed(v):
            return {
                "date": v["date"],
                "type": "completed",
                "tasks": v["tasks"]["completed"],
            }

        totals, completions = zip(
            *[(to_total(v), to_completed(v)) for v in data["versions"]]
        )
        stacked = list(totals + completions)
        values = json.dumps(stacked)

        template = self.template_path.read_text()
        html = template.replace("{{values}}", values)
        return html

    def open(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            path = temp.name + ".html"
            with open(path, "w") as f:
                f.write(self.to_html())
            native_open(path)
