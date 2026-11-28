Configured EbOs task services
=============================

The ``feat/ebos`` integration selects the six task services implemented in the
independent EbOs repository: ``ActivateTask``, ``TerminateTask``, ``ChainTask``,
``Schedule``, ``GetTaskID`` and ``GetTaskState``. This is a limited basic-task
profile over ESP-IDF **6.0.1**, traced to AUTOSAR Classic **R26-11** and its
inherited OSEK contracts. It does not establish full AUTOSAR OS conformance.

``StartOS``, ``ShutdownOS`` and ``GetActiveApplicationMode`` remain declarations
without implementations. ESP-IDF already runs the scheduler before product
entry. ``EbOs_OsInit`` creates dormant workers; it is not ``StartOS``.

Select compatible source revisions
----------------------------------

Use the integration feature manifest and its compatible module pins. The old
``ebos/1.0.0@neotech/prototype`` package lacks the task-service backend; it cannot
supply this feature. CUCEL must provide ``StatusType``, ``E_OK`` and
``STATUSTYPEDEFINED`` through ``Std_Types.h``. The manifest and
``_out/packages-resolved.json`` identify what is actually consumed.

On Windows, from ``neocam_csw``:

.. code-block:: powershell

   git switch feat/ebos
   .\neo.cmd setup
   .\neo.cmd check

On Ubuntu:

.. code-block:: bash

   git switch feat/ebos
   make setup
   make check

The launchers prepare the pinned SDK and package sources. Follow
:doc:`local-development` for fresh-machine prerequisites and repository access.
To edit EbOs independently, select a live checkout rather than editing its
fetched snapshot:

.. code-block:: powershell

   .\neo.cmd dev EbOs
   git -C ../modules/EbOs switch feat/ebos
   .\neo.cmd check

The Ubuntu equivalent is ``make dev MODULE=EbOs``, followed by the same Git
branch selection and ``make check``. The ignored ``packages.local.yml`` points
to that checkout; edits are visible immediately through the workspace link.
The rest of the feature manifest still selects compatible dependencies. A local
override does not update the committed baseline or its CI revisions. Use
:doc:`module-integration` to test a committed module revision in integration CI.

Keep product policy under Conf/EbOs
-----------------------------------

.. code-block:: text

   EbOs/Os/Os.h                     reusable standard task interface
   EbOs/OsShell/EbOs_Os.h           reusable profile types and lifecycle
   EbOs/Os_EspIdf/Os_EspIdf.c       ESP-IDF implementation

   Conf/EbOs/Os/Os_Cfg.h            product task IDs and declarations
   Conf/EbOs/Os/Os_Cfg.c            names, stacks, priorities, limits, entries
   Conf/EbOs/OsShell/EbOs_Cfg.*     existing native camera-worker configuration

``Os_Config`` contains immutable project configuration. Task IDs are table
indices. All configured tasks use one explicit core and distinct priorities;
stack sizes are bytes. The positive activation limit includes running and
queued work. EbOs validates this data by argument and includes no product
configuration header.

The current ``Os_Task_ProjectCheck`` entry checks identity/state, calls
``Schedule`` and terminates. It has **no automatic startup or activation**.
Camera, HTTP and Wi-Fi keep their existing execution paths. Building this
feature does not execute the probe or migrate those workers to basic tasks.

Run the explicit project probe
------------------------------

The following operations belong in a serialized product composition owner,
outside a configured basic-task entry. Include:

.. code-block:: c

   #include "EbOs.h"
   #include "EbOs_Os.h"
   #include "Os_Cfg.h"

First initialize. Continue only on ``NEO_OK``; validation/allocation failures do
not publish a partially active runtime:

.. code-block:: c

   Neo_StatusType init_status = EbOs_OsInit(&Os_Config);

Then release one activation. Continue only on ``E_OK``:

.. code-block:: c

   StatusType activation_status = ActivateTask(Os_Task_ProjectCheck);

Poll logical completion from the owner, yielding between observations. Read the
probe result **only after a successful state query reports SUSPENDED**. The
result is published before termination, so reading it immediately after
activation can observe an earlier result:

.. code-block:: c

   TaskStateType state = READY;
   StatusType state_status;
   do
   {
       state_status = GetTaskState(Os_Task_ProjectCheck, &state);
       if (state_status != E_OK)
       {
           break; /* Product owner handles the query failure. */
       }
       if (state != SUSPENDED)
       {
           EbOs_DelayOneTick();
       }
   } while (state != SUSPENDED);

   if (state_status == E_OK && state == SUSPENDED)
   {
       StatusType check_result = Os_ProjectCheckResult();
       /* E_OK means the probe's checks completed successfully. */
       (void)check_result;
   }

Once all configured work is suspended and no other callers can enter a task
service, deinitialize. Logical completion can precede the native worker's final
park; ``NEO_E_BUSY`` preserves the runtime for retry:

.. code-block:: c

   Neo_StatusType deinit_status;
   do
   {
       deinit_status = EbOs_OsDeinit();
       if (deinit_status == NEO_E_BUSY)
       {
           EbOs_DelayOneTick();
       }
   } while (deinit_status == NEO_E_BUSY);
   /* NEO_OK completes teardown; handle any other result in the owner. */

Initialization/deinitialization must be externally serialized with **every task
service call**, including calls from other SDK tasks. Before teardown, stop new
activations and wait for existing entries to finish their service calls. Keep
configuration, names and entry bindings valid and immutable until deinit returns
``NEO_OK``. Bound production polling/retry waits with the product's timeout
policy; expiry retains the runtime and its dependencies rather than force-deleting
workers. This guide does not add a call to existing product startup.

Task-entry rules and remaining standard gaps
--------------------------------------------

Entries are fully preemptive, nonblocking basic **C** tasks. They finish with
``TerminateTask`` or ``ChainTask``; success never returns, even through nested
helpers. The implementation uses internal C nonlocal exits, so do not cross
variable-length arrays or C++ objects requiring destruction. Release all native
locks first. The optional ``missing_end_hook`` receives the task ID and
``E_OS_MISSINGEND`` before retirement; it is a NeoTech diagnostic, not standard
``ErrorHook``. It may query identity/state but must return without blocking and
must not terminate, chain or schedule.

The profile rejects native ISR calls; no category 2 bridge is implemented.
Resources, spinlocks, extended-task events, non-preemptive/equal-priority
scheduling, OS-Application protection and core startup/shutdown remain outside
the profile. FreeRTOS mutexes do not implement AUTOSAR resource ceilings. A
null-output check does not supply writable-address protection. Read the
`independent EbOs requirements and compatibility matrix <https://neotech-vietnam.github.io/EbOs/requirements.html>`__
for precise implementation status and source requirement IDs.

Verify the implementation
-------------------------

``neo.cmd check`` / ``make check`` run integration host tests and firmware build
checks against selected revisions. Module-only regressions run with
``python test/run_host_tests.py`` from the EbOs checkout. They execute the real
task backend against controlled native fakes and check the source trace catalog.
They do not prove target scheduling or full AUTOSAR behavior.

The standalone ``EbOs/test/on_target`` acceptance app uses the real SDK and
includes ``main/os_tasks.c``: 50 activation/chain/return/deinit cycles on each
available core, one configured core at a time. Follow that module's
``test/README.md`` to build and deliberately flash this test firmware. Record
both monitor markers, ``PASS EBOS_CORE_TASK_SERVICES`` and
``PASS EBOS_DUAL_CORE_LIFECYCLE``, and verify normal NeoCam camera behavior
separately. SDK compilation alone leaves physical acceptance pending.
