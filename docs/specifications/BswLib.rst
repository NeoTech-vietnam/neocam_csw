.. _sws-bswlib:

Specification of BswLib
=======================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-BswLib``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``bswlib/1.0.0@neotech/prototype``
   * - Source commit
     - `bff049eb1af832e63b4f1f7f7cf182f3b4943cbc <https://github.com/NeoTech-vietnam/BswLib/tree/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc>`__

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

BswLib supplies MediaBuf, a bounded, reference-counted JPEG buffer pool shared by camera and delivery services.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - PSRAM
     - External pseudo-static RAM used for image payloads.
   * - Generation
     - Monotonic slot counter carried in a lease token.
   * - Lease
     - One live reference on a slot and generation.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../architecture/architecture`
* :doc:`../validation/optimization`

4 Constraints and assumptions
-----------------------------

* Initialize the pool before use. Serialize lifecycle calls after all clients are quiescent.
* Once a writer publishes a frame, consumers must treat the contents as immutable.
* The configured PSRAM buffers are CPU-copy storage. DMA suitability is **Unverified**.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines lease tokens and return values.
   * - :doc:`EbOs`
     - Serializes access to live slot state.
   * - ESP-IDF heap capabilities
     - Allocates byte-addressable PSRAM payloads.

**Source files**

`MediaBuf/MediaBuf.h <https://github.com/NeoTech-vietnam/BswLib/blob/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc/MediaBuf/MediaBuf.h>`__, `MediaBuf/MediaBuf.c <https://github.com/NeoTech-vietnam/BswLib/blob/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc/MediaBuf/MediaBuf.c>`__, `MediaBuf/MediaBuf_Backend.h <https://github.com/NeoTech-vietnam/BswLib/blob/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc/MediaBuf/MediaBuf_Backend.h>`__, `MediaBuf/MediaBuf_EspIdf.c <https://github.com/NeoTech-vietnam/BswLib/blob/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc/MediaBuf/MediaBuf_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/BswLib/blob/bff049eb1af832e63b4f1f7f7cf182f3b4943cbc/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-BswLib-001``
     - Reject stale tokens and keep leased storage alive.
     - :ref:`MediaBuf ownership and lifetime <sws-bswlib-ownership>`
     - ``camera_buffers`` host case in ``test/test_camera_buffers.c``.
   * - ``NEOCAM-SWS-BswLib-002``
     - Use independent slot ranges and reject teardown while leased.
     - :ref:`Separate preview and photo capacity <sws-bswlib-capacity>`
     - ``camera_buffers`` host case in ``test/test_camera_buffers.c``.

7 Functional specification
--------------------------

.. _sws-bswlib-ownership:

MediaBuf ownership and lifetime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acquisition reserves a free slot, increments its generation, and transfers one reference. Retain requires a live token; Release drops exactly one reference. Generation zero is reserved. Generation counters survive pool reinitialization, and a slot stops being reusable when its generation is exhausted.

.. _sws-bswlib-capacity:

Separate preview and photo capacity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preview and photo acquisitions search their own ranges. The pool allocates all payloads at initialization, rolls back partial allocation on failure, and refuses deinitialization until each reference count is zero.

Error classification
~~~~~~~~~~~~~~~~~~~~

Invalid arguments or malformed tokens return ``NEO_E_PARAM``. Stale or exhausted references can cause ``NEO_E_STATE``, ``NEO_E_BUSY``. A stopped pool reports ``NEO_E_NOT_READY`` from lease operations. Allocation failure returns ``NEO_E_MEMORY``.

8 API specification
-------------------

MediaBuf services
~~~~~~~~~~~~~~~~~

.. list-table:: MediaBuf_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Init``
   * - Syntax
     - ``Neo_StatusType MediaBuf_Init(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls after clients have quiesced.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_MEMORY`` May propagate a mutex creation error.
   * - Description
     - Allocates and initializes the configured pool.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Deinit``
   * - Syntax
     - ``Neo_StatusType MediaBuf_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls after clients have quiesced.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_BUSY`` May propagate a lock error.
   * - Description
     - Frees payload storage only when all references are released.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Acquire
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Acquire``
   * - Syntax
     - ``Neo_StatusType MediaBuf_Acquire(uint8 **data, Neo_BufferTokenType *token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - Writable pointer and one preview lease.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``
   * - Description
     - Reserves a preview slot.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_AcquirePhoto
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_AcquirePhoto``
   * - Syntax
     - ``Neo_StatusType MediaBuf_AcquirePhoto(uint8 **data, Neo_BufferTokenType *token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - Writable pointer and one photo lease.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``
   * - Description
     - Reserves a photo slot.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Retain
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Retain``
   * - Syntax
     - ``Neo_StatusType MediaBuf_Retain(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - ``token`` live token.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_STATE``, ``NEO_E_BUSY``
   * - Description
     - Creates one additional reference.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Release
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Release``
   * - Syntax
     - ``Neo_StatusType MediaBuf_Release(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - ``token`` live token.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_STATE``
   * - Description
     - Drops one reference.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Capacity
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Capacity``
   * - Syntax
     - ``uint32 MediaBuf_Capacity(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - ``token`` slot and generation.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Slot capacity in bytes, or zero for an invalid token or unavailable pool.
   * - Description
     - Looks up capacity for a live token.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_Outstanding
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_Outstanding``
   * - Syntax
     - ``uint32 MediaBuf_Outstanding(void)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Occupied slot count, zero if inactive, total configured slots on lock failure.
   * - Description
     - Counts slots with any references.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_References
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_References``
   * - Syntax
     - ``uint32 MediaBuf_References(void)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Total references saturated at ``UINT32_MAX``; zero if inactive and maximum on lock failure.
   * - Description
     - Counts references across both ranges.
   * - Available via
     - ``MediaBuf.h``

.. list-table:: MediaBuf_PreviewReferences
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``MediaBuf_PreviewReferences``
   * - Syntax
     - ``uint32 MediaBuf_PreviewReferences(void)``
   * - Execution and reentrancy
     - Synchronous. Concurrent active clients are serialized by the pool mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Preview references with the same saturation and failure semantics.
   * - Description
     - Counts references in the preview range.
   * - Available via
     - ``MediaBuf.h``

9 Sequence diagrams
-------------------

#. The writer acquires a preview or photo token and fills the writable slot.
#. The publisher keeps its original reference. Each consumer retains a separate reference.
#. Clients release their references. The slot becomes reusable after the final release.

10 Configuration specification
------------------------------

.. list-table:: Slot counts and capacities
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/BswLib/MediaBuf_Cfg.h``
   * - Type
     - Unsigned C constants
   * - Default
     - 4 preview slots of 512 KiB each and 1 photo slot of 1 MiB.
   * - Units or allowed values
     - Combined count must fit the 16-bit slot ID. Capacities must be positive and fit the 32-bit frame length.
   * - Effective
     - At firmware build time.
