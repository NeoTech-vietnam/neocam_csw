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
 * $Filename__:EbOs_Cfg.c$
 *
 * $Author____:Nguyen Ba Vu Thach$
 *
 * $Function__:NeoCam task-entry wiring for the EbOs native-task adapter.$
 *
 *************************************************************************
 * $Domain____:NeoTech$
 * $User______:Nguyen Ba Vu Thach$
 * $Date______:28.11.2026$
 * $Class_____:EbOs$
 * $Name______:EbOs_Cfg$
 * $Variant___:1.0.0$
 * $Revision__:2$
 * $Type______:C$
 * $State_____:PROTOTYPE$
 *
 *************************************************************************
 * List Of Changes
 *
 * $History
 *
 * 1.0.0; 1     28.11.2026 Nguyen Ba Vu Thach
 *   Add project-owned camera task policy and runnable wiring.
 * 1.0.0; 2     28.11.2026 Nguyen Ba Vu Thach
 *   Apply NeoTech source format and explicit integration requirements.
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

#include "EbOs_Cfg.h"
#include "CamPipe_TaskConfig.h"
#include "CamPipe_Backend.h"

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


/*
 **********************************************************************************************************************
 * Static function prototypes
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_CFG_00002]
 *  @details Run the camera producer until its cooperative stop completes.
 *  @param[in] argument Unused native-task argument.
 */
static void camera_producer(void *argument);

/*
 **********************************************************************************************************************
 * Local functions
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_CFG_00002]
 *  @details Project-owned runnable composition calls CamPipe for camera work.
 *           Each continuing iteration yields exactly one scheduler tick.
 *           The entry returns cooperatively for EbOs to retire its task.
 *  @param[in] argument Unused native-task argument.
 *  @return  No value. Return indicates that the producer has stopped.
 *  @note    Runs in task context; this is not an AUTOSAR basic-task body.
 */
static void camera_producer(void *argument)
{
    (void)argument;
    while (CamPipe_ProducerStep())
    {
        EbOs_DelayOneTick();
    }
}

/*
 **********************************************************************************************************************
 * Global variables
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_CFG_00001], TRACE[NEO_EBOS_CFG_00002]
 *  @details The project binds its entry function and policy to the native-task
 *           descriptor required by CamPipe. EbOs does not reference CamPipe.
 */
const EbOs_TaskConfigType CamPipe_TaskConfig = {
    .name = "NeoCamera",
    .stack_bytes = EBOS_CAMERA_STACK_BYTES,
    .priority = EBOS_CAMERA_PRIORITY,
    .core_affinity = NEOCAM_PRODUCER_CORE,
    .entry = camera_producer
};

/*
 **********************************************************************************************************************
 * Public functions
 **********************************************************************************************************************
 */
