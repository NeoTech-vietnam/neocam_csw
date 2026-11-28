#include "Platform_Types.h"

_Static_assert(sizeof(uint8) == 1, "uint8 must be 1 byte on ESP32-S3");
_Static_assert(sizeof(uint16) == 2, "uint16 must be 2 bytes on ESP32-S3");
_Static_assert(sizeof(uint32) == 4, "uint32 must be 4 bytes on ESP32-S3");
_Static_assert(sizeof(uint64) == 8, "uint64 must be 8 bytes on ESP32-S3");
