import json
import os
import typing
from distutils.dir_util import copy_tree

from lxml import etree


def report_results() -> dict:
    """
    Report the results by collecting and creating an HTML report.

    Returns:
        dict: Collected result data.
    """

    modules = os.getenv("module_names")

    if modules:
        modules = modules.split(",")
    else:
        print("No modules found")

    result = _collect_results(modules)
    json.dump(result, open(os.path.join("/workplace/mutmut_report/mutmut_report.json"), "w"))
    _create_html(modules, result)
    return result


def _collect_results(modules: typing.List[str]) -> dict:
    """
    Collect the results from the specified modules.

    Args:
        modules (list): List of module names to collect results from.

    Returns:
        dict: Aggregated result data.
    """
    data = []
    for module in modules:
        src = os.path.join("/workplace/mutmut_cache", module, "mutmut_report", "report.json")
        if not os.path.exists(src):
            print(f"Result for {module} does not exist")
            continue
        data += json.load(open(src))
    total = 0
    skipped = 0
    killed = 0
    survived = 0
    suspicious = 0
    timeout = 0
    arithmetic_mean = 0
    for d in data:
        total += d['total']
        skipped += d['skipped']
        killed += d['killed']
        survived += d['survived']
        suspicious += d['suspicious']
        timeout += d['timeout']
        if total == 0:
            killed_percent = 0
        else:
            killed_percent = killed / total * 100

        arithmetic_mean += killed_percent

    if total == 0:
        killed_percent = 0
    else:
        killed_percent = killed / total * 100
    arithmetic_mean = arithmetic_mean/len(data)
    return {"total": total, "killed": killed, "survived": survived, 
            "skipped": skipped, "timeout": timeout, "killed_percent": killed_percent, 
            "arithmetic_mean_killed": arithmetic_mean}


def _create_html(modules: typing.List[str], result: dict) -> None:
    """
    Create an HTML report from the collected results.

    Args:
        modules (list): List of module names included in the report.
        result (dict): Aggregated result data.
    """
    root = etree.Element("html")
    body = etree.SubElement(root, "body")
    header = etree.SubElement(body, "h1")
    header.text = f"{result['killed']} / {result['total']} killed, \
        arithmetic_mean: {result['arithmetic_mean_killed']:.1f}"
    merged_table = etree.SubElement(body, "table", id="merged_table")
    have_header = False
    for module in modules:
        file_name = os.path.join("/workplace/mutmut_cache", module, "mutmut_report", "index.html")
        if not os.path.exists(file_name):
            continue
        code_src = os.path.join("/workplace/mutmut_cache", module, "mutmut_report", "project")
        if os.path.exists(code_src):
            copy_tree(code_src, os.path.join("/workplace/mutmut_report", "project"))
        with open(file_name, "rb") as file:
            parser = etree.HTMLParser()
            tree = etree.parse(file, parser)

        tables = tree.xpath("//table")
        for table in tables:
            if not have_header:
                header_row = table.find("./thead/tr")
                merged_table.append(header_row)
                have_header = True

            rows = table.findall("./tbody/tr")[:]
            for row in rows:
                merged_table.append(row)

    with open(os.path.join("/workplace/mutmut_report/mutmut_report.html"), "wb") as merged_file:
        merged_file.write(etree.tostring(root, pretty_print=True))
    return


if __name__ == "__main__":
    report_results()