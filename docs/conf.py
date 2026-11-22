from pathlib import Path

import yaml

project = "NeoCam"
root_doc = "index"
language = "en"
nitpicky = True
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["specifications.css"]
# Search result snippets fetch pages, which browsers block for file:// previews.
html_show_search_summary = False

firmware_workflow = Path(__file__).resolve().parents[1] / ".github/workflows/integration.yml"
firmware_settings = yaml.safe_load(firmware_workflow.read_text(encoding="utf-8"))
sdk = firmware_settings["jobs"]["integration"]["with"]
sdk_version = sdk["idf-version"]
sdk_target = sdk["target"]
sdk_docs = f"https://docs.espressif.com/projects/esp-idf/en/{sdk_version}/{sdk_target}/"

rst_epilog = f"""
.. |esp-idf-version| replace:: ``{sdk_version}``
.. |esp-idf-target| replace:: ``{sdk_target}``
.. _Programming Guide: {sdk_docs}
.. _Installation and first build: {sdk_docs}get-started/index.html
.. _API Reference: {sdk_docs}api-reference/index.html
.. _ESP-IDF release notes: https://github.com/espressif/esp-idf/releases/tag/{sdk_version}
"""
