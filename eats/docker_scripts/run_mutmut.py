import importlib
import inspect
import json
import os
import sys

from mutmut import mutmut


def main(html_report="mutmut_report", json_report="mutmut_report/report.json"):
    """  # noqa: E501
    Runs mutation testing on a specified module and generates both an HTML and a JSON report.

    Parameters:
    html_report (str): The file path where the HTML report will be saved. Default is "mutmut_report".
    json_report (str): The file path where the JSON report will be saved. Default is "mutmut_report/report.json".

    Returns:
    None
    """
    sys.path.append(os.environ['PROJECT_ROOT'])
    module = importlib.import_module(os.environ['module_name'])
    mutmut.run([inspect.getfile(module)])
    mutmut.html(["Struct", "NamedStruct"], html_report)
    json.dump(mutmut.create_report(), open(json_report, "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
