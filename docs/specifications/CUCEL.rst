.. _sws-cucel:

Specification of CUCEL
======================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-CUCEL``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``cucel/1.0.0@neotech/prototype``
   * - Source commit
     - `4fdf73f84e656369b7a5ac5c77a4fa46c558a58c <https://github.com/NeoTech-vietnam/CUCEL/tree/4fdf73f84e656369b7a5ac5c77a4fa46c558a58c>`__

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

CUCEL supplies the platform and standard headers shared by NeoCam and the preprocessor protocol for grouping declarations into linker sections.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - CUCEL
     - Package for the common platform, standard types, and memory mapping headers.
   * - DROM
     - Flash-backed data read-only memory.
   * - DRAM
     - Internal data RAM.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* `AUTOSAR CP R24-11 Platform Types <https://www.autosar.org/fileadmin/standards/R24-11/CP/AUTOSAR_CP_SWS_PlatformTypes.pdf>`__
* `AUTOSAR CP R24-11 Standard Types <https://www.autosar.org/fileadmin/standards/R24-11/CP/AUTOSAR_CP_SWS_StandardTypes.pdf>`__
* `AUTOSAR CP R24-11 Memory Mapping <https://www.autosar.org/fileadmin/standards/R24-11/CP/AUTOSAR_CP_SWS_MemoryMapping.pdf>`__

4 Constraints and assumptions
-----------------------------

* The selected target is ESP32-S3 with a C implementation providing the standard integer and float definitions used by the headers.
* Section mapping uses GCC-compatible attributes and the product linker layout.
* Project types and status codes live in :doc:`NeoContracts`.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - ``stdint.h``, ``limits.h``, ``float.h``
     - Provide C integer types and numeric limits.
   * - ``Platform_Types.h``
     - Supplies the types imported by Std_Types.h.
   * - ``Conf/CUCEL/NeoCam_Sections.h``
     - Defines the target section attributes used by MemMap.h.

**Source files**

`Platform/Platform_Types.h <https://github.com/NeoTech-vietnam/CUCEL/blob/4fdf73f84e656369b7a5ac5c77a4fa46c558a58c/Platform/Platform_Types.h>`__, `Standard/Std_Types.h <https://github.com/NeoTech-vietnam/CUCEL/blob/4fdf73f84e656369b7a5ac5c77a4fa46c558a58c/Standard/Std_Types.h>`__, `MemMap/MemMap.h <https://github.com/NeoTech-vietnam/CUCEL/blob/4fdf73f84e656369b7a5ac5c77a4fa46c558a58c/MemMap/MemMap.h>`__, `module.cmake <https://github.com/NeoTech-vietnam/CUCEL/blob/4fdf73f84e656369b7a5ac5c77a4fa46c558a58c/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-CUCEL-001``
     - Publish common numeric and Boolean types.
     - :ref:`Platform type contract <sws-cucel-platform-types>`
     - ``platform_check`` in ``test/run_host_tests.py`` checks representative sizes and the selected CPU and byte order.
   * - ``NEOCAM-SWS-CUCEL-002``
     - Require matched, non-nested begin and end markers.
     - :ref:`Memory-section transitions <sws-cucel-sections>`
     - ``architecture_checks`` compiles invalid marker inputs.

7 Functional specification
--------------------------

.. _sws-cucel-platform-types:

Platform type contract
~~~~~~~~~~~~~~~~~~~~~~

The platform header selects a 32-bit CPU and least-significant-first bit and byte order. Exact-width signed and unsigned types cover 8, 16, 32 and 64 bits. The least-width families cover 8, 16 and 32 bits.

.. _sws-cucel-sections:

Memory-section transitions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Include ``MemMap.h`` with a single start marker, annotate declarations, then include it again with the corresponding stop marker. Unrecognized, nested and mismatched transitions produce preprocessor errors.

Error classification
~~~~~~~~~~~~~~~~~~~~

Memory mapping misuse fails at preprocessing. The type and symbol headers define no runtime error reporting.

8 API specification
-------------------

Platform and standard types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: boolean
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``boolean``
   * - Kind
     - Scalar
   * - Representation / range
     - ``_Bool`` with false and true values.
   * - Description
     - Platform Boolean type.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint8
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint8``
   * - Kind
     - Exact-width unsigned integer
   * - Representation / range
     - ``uint8_t``
   * - Description
     - 8 bits, from zero to 2^8 minus 1.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint8
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint8``
   * - Kind
     - Exact-width signed integer
   * - Representation / range
     - ``int8_t``
   * - Description
     - 8 bits, using the corresponding ``INT8_MIN`` and ``INT8_MAX`` bounds.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint16
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint16``
   * - Kind
     - Exact-width unsigned integer
   * - Representation / range
     - ``uint16_t``
   * - Description
     - 16 bits, from zero to 2^16 minus 1.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint16
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint16``
   * - Kind
     - Exact-width signed integer
   * - Representation / range
     - ``int16_t``
   * - Description
     - 16 bits, using the corresponding ``INT16_MIN`` and ``INT16_MAX`` bounds.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint32
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint32``
   * - Kind
     - Exact-width unsigned integer
   * - Representation / range
     - ``uint32_t``
   * - Description
     - 32 bits, from zero to 2^32 minus 1.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint32
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint32``
   * - Kind
     - Exact-width signed integer
   * - Representation / range
     - ``int32_t``
   * - Description
     - 32 bits, using the corresponding ``INT32_MIN`` and ``INT32_MAX`` bounds.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint64
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint64``
   * - Kind
     - Exact-width unsigned integer
   * - Representation / range
     - ``uint64_t``
   * - Description
     - 64 bits, from zero to 2^64 minus 1.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint64
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint64``
   * - Kind
     - Exact-width signed integer
   * - Representation / range
     - ``int64_t``
   * - Description
     - 64 bits, using the corresponding ``INT64_MIN`` and ``INT64_MAX`` bounds.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint8_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint8_least``
   * - Kind
     - Minimum-width unsigned integer
   * - Representation / range
     - ``uint_least8_t``
   * - Description
     - At least 8 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint8_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint8_least``
   * - Kind
     - Minimum-width signed integer
   * - Representation / range
     - ``int_least8_t``
   * - Description
     - At least 8 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint16_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint16_least``
   * - Kind
     - Minimum-width unsigned integer
   * - Representation / range
     - ``uint_least16_t``
   * - Description
     - At least 16 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint16_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint16_least``
   * - Kind
     - Minimum-width signed integer
   * - Representation / range
     - ``int_least16_t``
   * - Description
     - At least 16 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: uint32_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``uint32_least``
   * - Kind
     - Minimum-width unsigned integer
   * - Representation / range
     - ``uint_least32_t``
   * - Description
     - At least 32 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: sint32_least
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``sint32_least``
   * - Kind
     - Minimum-width signed integer
   * - Representation / range
     - ``int_least32_t``
   * - Description
     - At least 32 bits.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: float32
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``float32``
   * - Kind
     - Floating point
   * - Representation / range
     - ``float``
   * - Description
     - The header exposes limits and epsilon from ``FLT_*``. The host check verifies the 4-byte width.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: float64
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``float64``
   * - Kind
     - Floating point
   * - Representation / range
     - ``double``
   * - Description
     - The header exposes limits and epsilon from ``DBL_*``. The host check verifies the 8-byte width.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: VoidPtr
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``VoidPtr``
   * - Kind
     - Pointer
   * - Representation / range
     - ``void *``
   * - Description
     - Untyped mutable pointer.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: ConstVoidPtr
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``ConstVoidPtr``
   * - Kind
     - Pointer
   * - Representation / range
     - ``const void *``
   * - Description
     - Untyped pointer to read-only data.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: Std_ReturnType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Std_ReturnType``
   * - Kind
     - Scalar
   * - Representation / range
     - ``uint8``
   * - Description
     - Standard return container for ``E_OK``, ``E_NOT_OK``.
   * - Available via
     - ``Std_Types.h``

.. list-table:: Std_VersionInfoType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Std_VersionInfoType``
   * - Kind
     - Structure
   * - Representation / range
     - ``uint16`` vendor and module IDs, ``uint8`` version components.
   * - Description
     - Contains ``vendorID``, ``moduleID``, ``sw_major_version``, ``sw_minor_version``, ``sw_patch_version``.
   * - Available via
     - ``Std_Types.h``

Symbols and section controls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Target selection
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``CPU_TYPE``, ``CPU_BIT_ORDER``, ``CPU_BYTE_ORDER``
   * - Kind
     - Preprocessor symbols
   * - Selected values
     - ``CPU_TYPE_32``, ``LSB_FIRST``, ``LOW_BYTE_FIRST``
   * - Available via
     - ``Platform_Types.h``

.. list-table:: Platform constants
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``CPU_TYPE_8``, ``CPU_TYPE_16``, ``CPU_TYPE_32``, ``CPU_TYPE_64``, ``MSB_FIRST``, ``LSB_FIRST``, ``HIGH_BYTE_FIRST``, ``LOW_BYTE_FIRST``, ``TRUE``, ``FALSE``
   * - Kind
     - Integer selectors and Boolean literals
   * - Values
     - CPU widths are 8, 16, 32 and 64. Most-significant/high-first selectors are 0 and least-significant/low-first selectors are 1. Boolean macros are declared only when absent.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: Numeric limits
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - Unsigned minima, signed minima/maxima, and floating minimum, maximum and epsilon macros
   * - Kind
     - Preprocessor symbols
   * - Values
     - Unsigned minima are zero. Signed bounds use ``INTn_MIN/MAX`` and floating values use the C ``FLT_*``, ``DBL_*`` constants.
   * - Available via
     - ``Platform_Types.h``

.. list-table:: Standard constants
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``E_OK``, ``E_NOT_OK``, ``STD_HIGH``, ``STD_LOW``, ``STD_ACTIVE``, ``STD_IDLE``, ``STD_ON``, ``STD_OFF``, ``NULL_PTR``
   * - Values
     - Success 0, failure 1, each high/active/on value 1, each low/idle/off value 0, and a null pointer.
   * - Available via
     - ``Std_Types.h``

.. list-table:: Memory-section interface
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``NEOCAM_START_SEC_CONST_UNSPECIFIED``, ``NEOCAM_STOP_SEC_CONST_UNSPECIFIED``, ``NEOCAM_START_SEC_VAR_CLEARED_UNSPECIFIED``, ``NEOCAM_STOP_SEC_VAR_CLEARED_UNSPECIFIED``, ``NEOCAM_SECTION``
   * - Kind
     - Repeated-include preprocessor protocol
   * - Description
     - Set a marker and include the header to transition. Annotate declarations inside the range with ``NEOCAM_SECTION``.
   * - Available via
     - ``MemMap.h``

Not applicable. This module exposes compile-time definitions without callable services.

9 Sequence diagrams
-------------------

.. code-block:: c

   #define NEOCAM_START_SEC_CONST_UNSPECIFIED
   #include "MemMap.h"
   NEOCAM_SECTION const uint8 value = 1U;
   #define NEOCAM_STOP_SEC_CONST_UNSPECIFIED
   #include "MemMap.h"

10 Configuration specification
------------------------------

.. list-table:: Section placement
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/CUCEL/NeoCam_Sections.h``
   * - Type
     - GCC section attributes
   * - Default
     - ``.rodata.neocam`` for constants and ``.bss.neocam`` for cleared data.
   * - Units or allowed values
     - Flash DROM and internal DRAM respectively, as selected by the product linker.
   * - Effective
     - At firmware build time.

Appendix A. Applicability
-------------------------

Service IDs, scheduled entry points and ECUC configuration are inapplicable to these headers. The headers implement a platform-type and memory-mapping subset for NeoCam.
