.. _sws-bootctrl:

Specification of BootCtrl
=========================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-BootCtrl``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``bootctrl/1.0.0@neotech/prototype``
   * - Source commit
     - `3d55b742a1796dcd86b3bd984b342fb308ec0bb1 <https://github.com/NeoTech-vietnam/BootCtrl/tree/3d55b742a1796dcd86b3bd984b342fb308ec0bb1>`__

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

BootCtrl runs the configured NeoCam startup steps and stops them in reverse order. Its ESP-IDF adapter owns the product's NVS initialization stage.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - NVS
     - ESP-IDF non-volatile storage service.
   * - Rollback
     - Reverse cleanup of started or attempted stages after a failure.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/validation`

4 Constraints and assumptions
-----------------------------

* The composition owner serializes lifecycle operations and status reads. Use task context.
* The configuration array and callbacks must remain valid until cleanup completes. Each stop callback must handle an attempted start and allow retry.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines shared return codes.
   * - ESP-IDF NVS and logging
     - Initialize and deinitialize the default NVS partition and record native errors.
   * - ``Conf/__CONFIG/NeoCam_Composition.c``
     - Supplies the static step list and callbacks.

**Source files**

`BootCtrl.h <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/BootCtrl.h>`__, `BootCtrl.c <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/BootCtrl.c>`__, `BootCtrl_EspIdf.c <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/BootCtrl_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-BootCtrl-001``
     - Start steps in order and retain ownership when cleanup fails.
     - :ref:`Startup and reverse cleanup <sws-bootctrl-order>`
     - `test/test_boot_ctrl.c <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/test/test_boot_ctrl.c>`__
   * - ``NEOCAM-SWS-BootCtrl-002``
     - Initialize NVS and preserve storage on errors.
     - :ref:`NVS lifecycle <sws-bootctrl-nvs>`
     - `test/test_nvs.c <https://github.com/NeoTech-vietnam/BootCtrl/blob/3d55b742a1796dcd86b3bd984b342fb308ec0bb1/test/test_nvs.c>`__

7 Functional specification
--------------------------

.. _sws-bootctrl-order:

Startup and reverse cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

BootCtrl validates the whole step list before starting. If a start fails, rollback includes the failed step. A failed stop leaves that step and earlier dependencies active for retry. Status preserves the original failure, failed stage and first cleanup failure.

.. _sws-bootctrl-nvs:

NVS lifecycle
~~~~~~~~~~~~~

An initialized adapter skips redundant initialization. Failed native initialization or deinitialization is logged and maps to an I/O error. The adapter never erases the partition.

Error classification
~~~~~~~~~~~~~~~~~~~~

Invalid configuration returns ``NEO_E_PARAM``. Starting while stages remain owned returns ``NEO_E_STATE``. Start returns the failing start result even if rollback also fails. Stop returns the failing stop result.

8 API specification
-------------------

Types
~~~~~

.. list-table:: BootCtrl_StepType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``BootCtrl_StepType``
   * - Kind
     - Structure
   * - Representation / range
     - Stage name and start/stop function pointers.
   * - Description
     - Each callback returns a ``Neo_StatusType``.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_ConfigType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``BootCtrl_ConfigType``
   * - Kind
     - Structure
   * - Representation / range
     - Pointer to a step array and ``uint32`` count.
   * - Description
     - Configuration borrowed throughout ownership.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_StatusType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``BootCtrl_StatusType``
   * - Kind
     - Structure
   * - Representation / range
     - Primary and cleanup results, stage name and active count.
   * - Description
     - Snapshot of lifecycle progress and errors.
   * - Available via
     - ``BootCtrl.h``

Services
~~~~~~~~

.. list-table:: BootCtrl_Start
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``BootCtrl_Start``
   * - Syntax
     - ``Neo_StatusType BootCtrl_Start(const BootCtrl_ConfigType *config)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - ``config`` valid step list.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_STATE`` Otherwise the failed start result.
   * - Description
     - Starts the configured stages and rolls back on failure.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_Stop
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``BootCtrl_Stop``
   * - Syntax
     - ``Neo_StatusType BootCtrl_Stop(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK`` or the failing stop result.
   * - Description
     - Stops active stages in reverse order. Retrying begins at the failed stage.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_GetStatus
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``BootCtrl_GetStatus``
   * - Syntax
     - ``BootCtrl_StatusType BootCtrl_GetStatus(void)``
   * - Execution and reentrancy
     - Synchronous. Read from the serialized lifecycle context.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``BootCtrl_StatusType`` by value.
   * - Description
     - Returns the last result, cleanup result, stage and active count.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_PlatformInit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``BootCtrl_PlatformInit``
   * - Syntax
     - ``Neo_StatusType BootCtrl_PlatformInit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_IO``
   * - Description
     - Initializes ESP-IDF NVS once.
   * - Available via
     - ``BootCtrl.h``

.. list-table:: BootCtrl_PlatformDeinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``BootCtrl_PlatformDeinit``
   * - Syntax
     - ``Neo_StatusType BootCtrl_PlatformDeinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_IO``
   * - Description
     - Deinitializes ESP-IDF NVS when owned.
   * - Available via
     - ``BootCtrl.h``

9 Sequence diagrams
-------------------

:ref:`neocam-startup-sequence` shows the configured path. Each step returns to BootCtrl before the next begins.

10 Configuration specification
------------------------------

.. list-table:: Startup step list
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/__CONFIG/NeoCam_Composition.c``
   * - Type
     - ``BootCtrl_StepType`` array
   * - Default
     - NVS, JPEG pool, camera, RTE, application, Wi-Fi init, Wi-Fi start, producer, HTTP.
   * - Units or allowed values
     - Ordered named callbacks. Every entry provides a start and stop function.
   * - Effective
     - Compiled into the firmware and applied when the service starts.
