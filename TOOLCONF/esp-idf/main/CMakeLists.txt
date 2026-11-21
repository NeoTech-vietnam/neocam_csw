idf_component_register(
    SRCS "${PROJECT_DIR}/Conf/__CONFIG/main.c" "${PROJECT_DIR}/Conf/__CONFIG/NeoCam_Composition.c"
    INCLUDE_DIRS "${PROJECT_DIR}/Conf/__CONFIG"
    REQUIRES BSW Rte ApplicationLayer log
)
