#include "EbOs_Cfg.h"
#include "CamPipe_TaskConfig.h"
#include "CamPipe_Backend.h"

/* Project task/runnable wiring: camera work itself remains owned by CamPipe. */
static void camera_producer(void *argument)
{
    (void)argument;
    while (CamPipe_ProducerStep()) {
        EbOs_DelayOneTick();
    }
}

const EbOs_TaskConfigType CamPipe_TaskConfig = {
    .name = "NeoCamera",
    .stack_bytes = EBOS_CAMERA_STACK_BYTES,
    .priority = EBOS_CAMERA_PRIORITY,
    .core_affinity = NEOCAM_PRODUCER_CORE,
    .entry = camera_producer
};
