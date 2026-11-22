Contributing documentation
==========================

Build the site from the integration checkout with Python 3.12 or newer. Use
``python3`` in place of ``python`` if that is the command on your Ubuntu system.
The build works from a clean integration checkout without the SDK or any of the
module repos. A virtual environment keeps the documentation dependency separate.

.. code-block:: text

   python -m pip install -r docs/requirements.txt
   python -m sphinx -b html -n -W --keep-going docs _build/docs/html

Open ``_build/docs/html/index.html`` in a browser. The **NeoCam documentation**
Actions workflow attaches the HTML as ``neocam-docs-html``. The **Deploy documentation**
workflow publishes the integration guides and package catalog on GitHub Pages.
Update a package's own ``docs/specification.rst`` when its interfaces change.
Update the integration baseline when ``packages.yml`` selects a new release.

Write pages in reStructuredText and add each new page to its branch's
``toctree``. Use ``:doc:`` for links to pages, ``:ref:`` for stable labels, and
captioned ``list-table`` directives for specification tables. Follow the section
order and field names in :doc:`../specifications/CUCEL` and
:doc:`../specifications/CamPipe`. Use a module-prefixed label for a behavior
referenced by its trace table and by other modules.

When updating a module pin, check the selected commit's public headers,
implementation, and tests against its specification. Check product settings
against ``Conf``, ``GConf`` and ``sdkconfig.defaults``. Record the selected ref,
commit and the nature of the change in the specification. A development link can
select a different revision from the manifest. Record a reason for **Not
applicable** entries and identify unsupported assertions as **Unverified**.

The architecture figures pair editable ``.mmd`` sources with committed SVGs.
After editing a source, regenerate the corresponding SVG with Mermaid CLI and
open it in the HTML build. For example, from the integration root:

.. code-block:: text

   mmdc -i docs/architecture/diagrams/dependencies.mmd -o docs/architecture/diagrams/dependencies.svg

Editorial references
--------------------

* `ESP-IDF documentation contribution guide
  <https://github.com/espressif/esp-idf/blob/v6.0.1/docs/en/contribute/documenting-code.rst>`__
* `AUTOSAR CP R22-11 Platform Types
  <https://www.autosar.org/fileadmin/standards/R22-11/CP/AUTOSAR_SWS_PlatformTypes.pdf>`__
* `AUTOSAR CP R22-11 General Specification of Basic Software Modules
  <https://www.autosar.org/fileadmin/standards/R22-11/CP/AUTOSAR_SWS_BSWGeneral.pdf>`__
* `AUTOSAR CP R22-11 Communication
  <https://www.autosar.org/fileadmin/standards/R22-11/CP/AUTOSAR_SWS_COM.pdf>`__
