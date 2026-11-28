/*<NeoTechHead>
 *************************************************************************
 *                              NeoTech
 *************************************************************************
 *
 * /   / /////  ///  ///// /////  ///  /   /
 * //  / /     /   /   /   /     /   / /   /
 * / / / ///   /   /   /   ///   /     /////
 * /  // /     /   /   /   /     /   / /   /
 * /   / /////  ///    /   /////  ///  /   /
 *
 *************************************************************************
 * Administrative Information
 *************************************************************************
 *
 * $Filename__:Os_Cfg.c$
 *
 * $Author____:Nguyen Ba Vu Thach$
 *
 * $Function__:NeoCam-owned task values and basic-task entry wiring.$
 *
 *************************************************************************
 * $Domain____:NeoTech$
 * $User______:Nguyen Ba Vu Thach$
 * $Date______:28.11.2026$
 * $Class_____:EbOs$
 * $Name_____:Os_Cfg$
 * $Variant___:1.1.0$
 * $Revision__:1$
 * $Type_____:C$
 * $State_____:DRAFT$
 *
 *************************************************************************
 * List Of Changes
 *
 * $History
 *
 * 1.1.0; 1     28.11.2026 Nguyen Ba Vu Thach
 *   Add the explicitly limited ESP-IDF basic-task runtime profile.
 *
 * $
 *
 *************************************************************************
</NeoTechHead>*/

/*
 **********************************************************************************************************************
 * Includes
 **********************************************************************************************************************
 */

#include "Os_Cfg.h"
#include <stdatomic.h>

/*
 **********************************************************************************************************************
 * Defines / Macros
 **********************************************************************************************************************
 */

/*
 **********************************************************************************************************************
 * Local types
 **********************************************************************************************************************
 */

/*
 **********************************************************************************************************************
 * Static variables
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details The check is explicit; no application task is activated on load.
 */
static _Atomic StatusType project_check_result = E_OS_STATE;

/*
 **********************************************************************************************************************
 * Static function prototypes
 **********************************************************************************************************************
 */

static void Os_ProjectCheckEntry(void);

/*
 **********************************************************************************************************************
 * Local functions
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details Project-owned wiring for a small on-demand bring-up check. Real
 *           application runnables can be bound in this folder in a later step.
 *           Camera, HTTP and Wi-Fi workers keep their existing native lifecycles.
 */
static void Os_ProjectCheckEntry(void)
{
    TaskType task_id = INVALID_TASK;
    TaskStateType state = SUSPENDED;
    StatusType result = GetTaskID(&task_id);
    if (result == E_OK && task_id != Os_Task_ProjectCheck)
    {
        result = E_OS_ID;
    }
    if (result == E_OK)
    {
        result = GetTaskState(task_id, &state);
    }
    if (result == E_OK && state != RUNNING)
    {
        result = E_OS_STATE;
    }
    if (result == E_OK)
    {
        result = Schedule();
    }
    atomic_store_explicit(&project_check_result, result, memory_order_release);
    (void)TerminateTask();
}

/*
 **********************************************************************************************************************
 * Public functions
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details All concrete values belong to this project configuration.
 */
static const EbOs_OsTaskConfigType Os_TaskConfig[] = {
    {
        .name = "NeoCamProjectCheck",
        .stack_bytes = 4096U,
        .priority = 4U,
        .activation_limit = 2U,
        .entry = Os_ProjectCheckEntry
    }
};

const EbOs_OsConfigType Os_Config = {
    .tasks = Os_TaskConfig,
    .task_count = sizeof(Os_TaskConfig) / sizeof(Os_TaskConfig[0]),
    .core_affinity = 0,
    .missing_end_hook = NULL_PTR
};

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details Acquire the result published by the configured project-check task.
 */
StatusType Os_ProjectCheckResult(void)
{
    return atomic_load_explicit(&project_check_result, memory_order_acquire);
}
