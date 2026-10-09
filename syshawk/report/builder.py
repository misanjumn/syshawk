"""Assemble all collector data and render the HTML report."""

from __future__ import annotations
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def build_report(data: dict, output_path: str) -> None:
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("template.html")
    html = template.render(data=data, data_json=json.dumps(data))
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
