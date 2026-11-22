.. _sws-httpsrv:

Specification of HttpSrv
========================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-HttpSrv``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``httpsrv/1.0.0@neotech/prototype``
   * - Source commit
     - `42e4eb03096d2a8894149ceb7073e347280870b2 <https://github.com/NeoTech-vietnam/HttpSrv/tree/42e4eb03096d2a8894149ceb7073e347280870b2>`__

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

HttpSrv owns ESP-IDF HTTP transport for NeoCam. It attaches application callbacks, registers routes, and runs one asynchronous MJPEG worker and one asynchronous image worker.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - HTTP
     - Hypertext Transfer Protocol.
   * - MJPEG
     - Multipart stream of JPEG frames.
   * - Async request
     - Request transferred from the server handler to a worker.
   * - Send deadline
     - Absolute transport deadline for one frame or image payload.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/optimization`

4 Constraints and assumptions
-----------------------------

* Start and stop belong to the composition owner. Keep callback targets and camera resources alive until stop succeeds.
* The stream and image workers can run concurrently. A second request for an occupied worker is rejected.
* The image send deadline begins after the capture callback returns. It does not bound capture or profile restoration time.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines callbacks, frame leases and result codes.
   * - :doc:`LocalTime`
     - Supplies send and shutdown deadlines.
   * - :doc:`Rte`
     - Supplies the product's wired HTTP port table.
   * - ESP-IDF HTTP server, lwIP and FreeRTOS
     - Provide route handlers, sockets, worker tasks and the state lock.

**Source files**

`HttpSrv.h <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv.h>`__, `HttpSrv_ConfigTypes.h <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv_ConfigTypes.h>`__, `HttpSrv.c <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv.c>`__, `HttpSrv_EspIdf.c <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv_EspIdf.c>`__, `HttpSrv_Internal.h <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv_Internal.h>`__, `HttpSrv_MemMap.h <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/HttpSrv_MemMap.h>`__, `module.cmake <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-HttpSrv-001``
     - Keep image transfer work off the synchronous server task.
     - :ref:`Route registration and separation <sws-httpsrv-routes>`
     - `test/test_http_srv.c <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/test/test_http_srv.c>`__
   * - ``NEOCAM-SWS-HttpSrv-002``
     - Release a borrowed frame and finish the async request on failure.
     - :ref:`Bounded send and lease cleanup <sws-httpsrv-leases>`
     - `test/test_http_srv.c <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/test/test_http_srv.c>`__
   * - ``NEOCAM-SWS-HttpSrv-003``
     - Keep the server live when asynchronous workers have not quiesced.
     - :ref:`Quiescent shutdown <sws-httpsrv-shutdown>`
     - `test/test_http_srv.c <https://github.com/NeoTech-vietnam/HttpSrv/blob/42e4eb03096d2a8894149ceb7073e347280870b2/test/test_http_srv.c>`__

7 Functional specification
--------------------------

.. _sws-httpsrv-routes:

Route registration and separation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The HTTP task serves dashboard, metrics and profile control. Stream and image requests claim separate worker slots. The image slot is shared by preview capture and still photo. Application handlers operate through the configured port table.

.. _sws-httpsrv-leases:

Bounded send and lease cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Worker sends use absolute deadlines and nonblocking socket writes. A served frame is released once whether sending succeeds or fails. Worker cleanup completes the async request and frees the worker slot.

.. _sws-httpsrv-shutdown:

Quiescent shutdown
~~~~~~~~~~~~~~~~~~

Stop marks the transport stopping and rejects new worker requests. It waits to the configured deadline for async workers and only then invokes the server stop. A timeout leaves state allocated for retry.

Error classification
~~~~~~~~~~~~~~~~~~~~

Start reports malformed ports or settings, existing ownership, allocation errors and native start/route failures via ``NEO_E_PARAM``, ``NEO_E_STATE``, ``NEO_E_MEMORY``, ``NEO_E_IO``. Stop can return ``NEO_E_TIMEOUT`` while workers remain active or ``NEO_E_IO`` if native stop fails. An occupied worker produces HTTP 503.

8 API specification
-------------------

.. list-table:: HttpSrv_ConfigType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``HttpSrv_ConfigType``
   * - Kind
     - Structure
   * - Representation / range
     - ``uint16`` port and socket timeout, ``uint32`` stack and deadline fields.
   * - Description
     - HTTP backend settings.
   * - Available via
     - ``HttpSrv_ConfigTypes.h``

.. list-table:: HttpSrv_Config
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``HttpSrv_Config``
   * - Kind
     - Product configuration object
   * - Description
     - Compiled settings owned by the integration repository.
   * - Available via
     - ``HttpSrv_ConfigTypes.h``

.. list-table:: HttpSrv_Start
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``HttpSrv_Start``
   * - Syntax
     - ``Neo_StatusType HttpSrv_Start(const Neo_HttpPortsType *ports)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - ``ports`` complete callback table, copied on start.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_STATE``, ``NEO_E_MEMORY``, ``NEO_E_IO``
   * - Description
     - Starts the server and registers the default routes.
   * - Available via
     - ``HttpSrv.h``

.. list-table:: HttpSrv_Stop
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``HttpSrv_Stop``
   * - Syntax
     - ``Neo_StatusType HttpSrv_Stop(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_TIMEOUT``, ``NEO_E_IO``
   * - Description
     - Waits for workers, stops the server and releases its lock.
   * - Available via
     - ``HttpSrv.h``

HTTP endpoints
~~~~~~~~~~~~~~

.. list-table:: Provided endpoints
   :header-rows: 1

   * - Method and path
     - Contract
   * - ``GET /``
     - Dashboard HTML.
   * - ``GET /metrics``
     - Diagnostic JSON.
   * - ``GET /stream``
     - Multipart JPEG preview, one active stream.
   * - ``GET /capture``
     - One current preview JPEG.
   * - ``GET /photo``
     - Full-resolution JPEG from the application photo callback.
   * - ``GET /api/profile``
     - Current and requested profile, state and presets.
   * - ``POST /api/profile``
     - Accepts a JSON profile selection and returns HTTP 202 on admission.

9 Sequence diagrams
-------------------

:ref:`The product sequence diagrams <neocam-runtime-sequences>` show both worker paths and their frame release points.

10 Configuration specification
------------------------------

.. list-table:: HTTP server and worker settings
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/HttpSrv/HttpSrv_Cfg.c``
   * - Type
     - ``HttpSrv_ConfigType``
   * - Default
     - TCP port 80, socket wait 2 s, worker stack 6144 B, stop wait 10000 ms, stream frame send 500 ms and image send 5000 ms.
   * - Units or allowed values
     - Positive port and timeouts, worker stack at least 4096 bytes.
   * - Effective
     - Compiled into the firmware and applied when the service starts.
