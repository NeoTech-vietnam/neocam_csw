.. _sws-localtime:

Specification of LocalTime
==========================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-LocalTime``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``localtime/1.0.0@neotech/prototype``
   * - Source commit
     - `3439e60e19a3e3c02d47d861454ef61b8633c422 <https://github.com/NeoTech-vietnam/LocalTime/tree/3439e60e19a3e3c02d47d861454ef61b8633c422>`__

.. list-table:: Document change history
   :header-rows: 1

   * - Date
     - Revision
     - Description
   * - 2026-11-22
     - 1.0
     - Initial specification of the manifest-selected implementation.

.. contents:: Contents
   :local:
   :depth: 2

1 Introduction and functional overview
--------------------------------------

LocalTime exposes a monotonic elapsed-time reading for captures, worker deadlines and diagnostics.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - Monotonic time
     - Elapsed time on a local clock without wall-clock adjustment.
   * - µs
     - Microseconds.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../architecture/architecture`

4 Constraints and assumptions
-----------------------------

* Use the reading for durations on a single boot. It carries no calendar time or cross-device synchronization.
* Clock accuracy under product operating conditions is **Unverified** in this specification.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Supplies integer types.
   * - ESP-IDF esp_timer
     - Supplies microseconds since timer initialization.

**Source files**

`LocalTime.h <https://github.com/NeoTech-vietnam/LocalTime/blob/3439e60e19a3e3c02d47d861454ef61b8633c422/LocalTime.h>`__, `LocalTime_EspIdf.c <https://github.com/NeoTech-vietnam/LocalTime/blob/3439e60e19a3e3c02d47d861454ef61b8633c422/LocalTime_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/LocalTime/blob/3439e60e19a3e3c02d47d861454ef61b8633c422/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-LocalTime-001``
     - Return the backend elapsed timer value in microseconds.
     - :ref:`Elapsed-time read <sws-localtime-timebase>`
     - `LocalTime_EspIdf.c <https://github.com/NeoTech-vietnam/LocalTime/blob/3439e60e19a3e3c02d47d861454ef61b8633c422/LocalTime_EspIdf.c>`__. Host integrations substitute a test clock.

7 Functional specification
--------------------------

.. _sws-localtime-timebase:

Elapsed-time read
~~~~~~~~~~~~~~~~~

The wrapper reads ``esp_timer_get_time`` and casts it to ``uint64``. It maintains no module state.

Error classification
~~~~~~~~~~~~~~~~~~~~

The API has no error return or local error state.

8 API specification
-------------------

.. list-table:: LocalTime_GetUs
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``LocalTime_GetUs``
   * - Syntax
     - ``uint64 LocalTime_GetUs(void)``
   * - Execution and reentrancy
     - Synchronous, stateless read. No NeoCam lock is acquired.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``uint64`` elapsed microseconds.
   * - Description
     - Returns the ESP-IDF local timer reading.
   * - Available via
     - ``LocalTime.h``

9 Sequence diagrams
-------------------

Not applicable. The module does not coordinate a multi-step runtime interaction.

10 Configuration specification
------------------------------

Not applicable. The module exposes no product settings.
