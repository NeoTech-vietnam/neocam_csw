#ifndef EBOS_CFG_H
#define EBOS_CFG_H

/* Project execution policy. EbOs supplies types and validation, not these values. */
#define EBOS_CAMERA_STACK_BYTES 8192U
#define EBOS_CAMERA_PRIORITY 5U
#ifndef NEOCAM_PRODUCER_CORE
#define NEOCAM_PRODUCER_CORE (-1)
#endif

_Static_assert(NEOCAM_PRODUCER_CORE >= -1 && NEOCAM_PRODUCER_CORE <= 1,
               "Producer affinity must be unpinned, core 0, or core 1");

#endif
