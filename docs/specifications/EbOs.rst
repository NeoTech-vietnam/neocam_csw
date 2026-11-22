.. _sws-ebos:

Specification of EbOs
=====================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-EbOs``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``ebos/1.0.0@neotech/prototype``
   * - Source commit
     - `3b0efc83e949a98366492b2a6c3315daa05e5554 <https://github.com/NeoTech-vietnam/EbOs/tree/3b0efc83e949a98366492b2a6c3315daa05e5554>`__

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

EbOs provides task delays and opaque, non-recursive mutexes backed by FreeRTOS.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - Tick
     - Scheduler time unit.
   * - Mutex
     - Mutual-exclusion object with task ownership.
   * - ISR
     - Interrupt service routine.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`

4 Constraints and assumptions
-----------------------------

* Use from task context. The locking task releases its own mutex.
* Creation and deletion require serialized ownership and quiescent users.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Supplies status and platform types.
   * - ESP-IDF FreeRTOS and heap capabilities
     - Provide semaphore, task delay and internal-memory allocation.

**Source files**

`EbOs.h <https://github.com/NeoTech-vietnam/EbOs/blob/3b0efc83e949a98366492b2a6c3315daa05e5554/EbOs.h>`__, `EbOs_EspIdf.c <https://github.com/NeoTech-vietnam/EbOs/blob/3b0efc83e949a98366492b2a6c3315daa05e5554/EbOs_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/EbOs/blob/3b0efc83e949a98366492b2a6c3315daa05e5554/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-EbOs-001``
     - Provide bounded waits and an explicit indefinite mutex wait.
     - :ref:`Mutex and delay behavior <sws-ebos-mutex>`
     - `EbOs_EspIdf.c <https://github.com/NeoTech-vietnam/EbOs/blob/3b0efc83e949a98366492b2a6c3315daa05e5554/EbOs_EspIdf.c>`__. Portable integration tests use a backend fake.

7 Functional specification
--------------------------

.. _sws-ebos-mutex:

Mutex and delay behavior
~~~~~~~~~~~~~~~~~~~~~~~~

Finite durations round up to scheduler ticks and saturate below ``portMAX_DELAY``. Zero is a nonblocking take. ``EBOS_WAIT_FOREVER`` requests the backend's maximum mutex wait. The wrapper lives in internal memory.

Error classification
~~~~~~~~~~~~~~~~~~~~

Create rejects a null output and reports allocation failure. A null lock handle returns ``NEO_E_PARAM``. A failed semaphore take maps to ``NEO_E_TIMEOUT``. Unlock and delete ignore null handles.

8 API specification
-------------------

.. list-table:: EbOs_MutexType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``EbOs_MutexType``
   * - Kind
     - Opaque pointer
   * - Representation / range
     - ``struct EbOs_Mutex *``
   * - Description
     - Opaque wrapper for a native mutex.
   * - Available via
     - ``EbOs.h``

.. list-table:: EBOS_WAIT_FOREVER
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``EBOS_WAIT_FOREVER``
   * - Kind
     - Timeout sentinel
   * - Value
     - ``UINT32_MAX``
   * - Available via
     - ``EbOs.h``

.. list-table:: EbOs_MutexCreate
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``EbOs_MutexCreate``
   * - Syntax
     - ``Neo_StatusType EbOs_MutexCreate(EbOs_MutexType *out)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``out`` created handle, or null after allocation failure.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_MEMORY``
   * - Description
     - Creates the wrapper and native mutex.
   * - Available via
     - ``EbOs.h``

.. list-table:: EbOs_MutexLock
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``EbOs_MutexLock``
   * - Syntax
     - ``Neo_StatusType EbOs_MutexLock(EbOs_MutexType mutex, uint32 timeout_ms)``
   * - Execution and reentrancy
     - Synchronous task-context call. Keep the object alive throughout the call.
   * - Parameters (in)
     - ``mutex`` handle, ``timeout_ms`` finite milliseconds or the indefinite sentinel.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_TIMEOUT``
   * - Description
     - Takes the mutex.
   * - Available via
     - ``EbOs.h``

.. list-table:: EbOs_MutexUnlock
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``EbOs_MutexUnlock``
   * - Syntax
     - ``void EbOs_MutexUnlock(EbOs_MutexType mutex)``
   * - Execution and reentrancy
     - Synchronous task-context call. Keep the object alive throughout the call.
   * - Parameters (in)
     - ``mutex`` handle owned by the current task.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Releases the native mutex.
   * - Available via
     - ``EbOs.h``

.. list-table:: EbOs_MutexDelete
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``EbOs_MutexDelete``
   * - Syntax
     - ``void EbOs_MutexDelete(EbOs_MutexType mutex)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - ``mutex`` quiescent handle.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Frees the native mutex and wrapper.
   * - Available via
     - ``EbOs.h``

.. list-table:: EbOs_Delay
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``EbOs_Delay``
   * - Syntax
     - ``void EbOs_Delay(uint32 ms)``
   * - Execution and reentrancy
     - Synchronous. Different tasks may delay independently.
   * - Parameters (in)
     - ``ms`` duration in milliseconds.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Delays the current task for the computed tick count.
   * - Available via
     - ``EbOs.h``

9 Sequence diagrams
-------------------

#. The owner creates a mutex and publishes the handle.
#. A client takes the mutex, performs protected work, and releases it.
#. After all clients are quiescent, the owner deletes the mutex.

10 Configuration specification
------------------------------

.. list-table:: Scheduler tick frequency
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``sdkconfig.defaults``
   * - Type
     - ESP-IDF SDK configuration
   * - Default
     - The firmware inherits the SDK default. The local ESP32-S3 configuration resolves to 100 Hz.
   * - Units or allowed values
     - Ticks per second, from ``configTICK_RATE_HZ``.
   * - Effective
     - At firmware build time.
