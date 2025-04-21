/**************************************************************************************

      II    N     N     N     N      OOOO      SSSSS     EEEEE    N     N    TTTTTTT
     II    NNN   N     NNN   N    OO    OO    S         E        NNN   N       T
    II    N NN  N     N NN  N    OO    OO    SSSSS     EEE      N NN  N       T
   II    N  NN N     N  NN N    OO    OO        S     E        N  NN N       T
  II    N    NN     N    NN      OOOO      SSSSS     EEEEE    N    NN       T
                       copyright (c) 2011-2018, InnoSenT GmbH
                                 all rights reserved

***************************************************************************************

    filename:		itl_if.h
    brief:          Calls for tracking.
    creation:		22.02.2018
    author:			Jonas Kubo
    version:		v1.0
    last edit:		21.03.2018
    last editor:	Jonas Kubo
    change:			Compilation Date receive function added.

**************************************************************************************/

#ifndef ITL_IF_H
#define ITL_IF_H

/**************************************************************************************
 includes
**************************************************************************************/
#include "bt_basic_types.h"
#include "bt_structs_if.h"

/**************************************************************************************
 defines
**************************************************************************************/
#ifdef _WIN32
    #ifdef INNOSENT_TRACKER_LIBRARY
        #define ITL_EXPORT __declspec(dllexport)
    #else
        #define ITL_EXPORT __declspec(dllimport)
    #endif
#else
    #define ITL_EXPORT
#endif


#ifdef __cplusplus
extern "C" {
#endif


/**************************************************************************************
 typedefs
**************************************************************************************/
typedef enum {
    ITL_OK = 0,
    ITL_ERROR_PROCESSING,
    ITL_ERROR_MEMORY_ALLOCATION,
    ITL_ERROR_PARAMETER,
    ITL_ERROR_STRUCT_SIZE,
    ITL_ERROR_PRODUCT_CODE
}ITLResult_t;

typedef enum{
    ITL_PRODUCT_iSYS5011  = 5011u,
    ITL_PRODUCT_iSYS5021  = 5021u
}ITLProductCode_t;

/**************************************************************************************
 API functions
**************************************************************************************/

ITL_EXPORT ITLResult_t itl_init_tracker(float32_it cycleTime_s);
ITL_EXPORT ITLResult_t itl_execute_tracker(bt_target_list_rv_t *pTargetList, uint16_it nrOfTargets);
ITL_EXPORT ITLResult_t itl_receive_track_list(bt_ext_track_list_t *pTrackList, uint16_it *pNrOfTracks);

ITL_EXPORT ITLResult_t itl_set_ignore_zones(bt_ignore_zone_t *pIgnoreZones, uint16_it nrOfIgnoreZones);
ITL_EXPORT ITLResult_t itl_get_ignore_zones(bt_ignore_zone_t *pIgnoreZones);

ITL_EXPORT ITLResult_t itl_reset_tracks();

ITL_EXPORT ITLResult_t itl_set_default_values(ITLProductCode_t productCode);
ITL_EXPORT ITLResult_t itl_set_installation_height(float32_it height);
ITL_EXPORT ITLResult_t itl_get_installation_height(float32_it *pHeight);
ITL_EXPORT ITLResult_t itl_set_installation_angle(float32_it angle);
ITL_EXPORT ITLResult_t itl_get_installation_angle(float32_it *pAngle);

#ifdef __cplusplus
}
#endif

#endif // ITL_H
