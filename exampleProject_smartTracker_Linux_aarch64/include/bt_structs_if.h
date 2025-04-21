/**************************************************************************************

      II    N     N     N     N      OOOO      SSSSS     EEEEE    N     N    TTTTTTT
     II    NNN   N     NNN   N    OO    OO    S         E        NNN   N       T
    II    N NN  N     N NN  N    OO    OO    SSSSS     EEE      N NN  N       T
   II    N  NN N     N  NN N    OO    OO        S     E        N  NN N       T
  II    N    NN     N    NN      OOOO      SSSSS     EEEEE    N    NN       T
                       copyright (c) 2011-2018, InnoSenT GmbH
                                 all rights reserved

***************************************************************************************

    filename:       bt_structs_if.h
    brief:          interface defines and structs used in tracker environment
    creation:		27.08.2018
    author:			Jonas Kubo
    version:        v1.0
    last edit:      27.08.2018
    last editor:    Jonas Kubo
    change:         Number of targets and tracks added

***************************************************************************************
*/
#ifndef ITL_STRUCTS_IF_H
#define ITL_STRUCTS_IF_H

/**************************************************************************************
  includes
**************************************************************************************/

#include "bt_basic_types.h"

/**************************************************************************************
 defines
**************************************************************************************/

/* number of targets and tracks */
#define BT_MAX_NR_OF_TARGETS (256u)
#define BT_MAX_NR_OF_TRACKS  (64u)

/* ignore zones */
#define BT_MAX_NR_OF_IGNORE_ZONES (10u)
#define BT_MAX_NR_OF_POINTS_PER_IGNORE_ZONE (10u)


/**************************************************************************************
 enums
**************************************************************************************/
/* product code */
typedef enum{
    BT_PRODUCT_iSYS5011  = 5011u,
    BT_PRODUCT_iSYS5021  = 5021u
}BTProductCode_t;

/* track class */
typedef enum bt_track_class{
    BT_TRACK_CLASS_UNCLASSIFIED = 0u,
    BT_TRACK_CLASS_PEDESTRIAN   = 1u,
    BT_TRACK_CLASS_VEHICLE      = 2u,
    BT_TRACK_CLASS_OTHER        = 3u,
}bt_track_class_t;


/**************************************************************************************
 structs
**************************************************************************************/

/* RV target list received from sensor */
typedef struct bt_target_list_rv{
    float32_it f32_rcs_m2;              /* [m²] */
    float32_it f32_range_m;             /* [m]*/
    float32_it f32_velocity_mps;		/* [m/s] */
    float32_it f32_angleAzimuth_deg;	/* [deg] */
    float32_it f32_reserved1;
    float32_it f32_reserved2;
}bt_target_list_rv_t;

/* external track list */
typedef struct bt_ext_track_list{
    /* track identifier */
    uint32_it ui32_objectID;
    /* additional states */
    uint16_it ui16_ageCount;
    uint16_it ui16_predictionCount;
    uint16_it ui16_staticCount;
    float32_it f32_trackQuality;
    bt_track_class_t classID;
    /* track position and velocity */
    float32_it f32_positionX_m;
    float32_it f32_positionY_m;
    float32_it f32_velocityX_mps;
    float32_it f32_velocityY_mps;
    float32_it f32_directionX;
    float32_it f32_directionY;
}bt_ext_track_list_t;

/* ignore zone struct */
typedef struct bt_ignore_zone{
    bool_it b_active;
    uint16_it ui16_nrOfVertices;
    v2d_f32_it v2d_min;     /* optimization for faster ignore zone check */
    v2d_f32_it v2d_max;     /* optimization for faster ignore zone check */
    v2d_f32_it v2d_vertex[BT_MAX_NR_OF_POINTS_PER_IGNORE_ZONE];     /* polygon vertex points */
}bt_ignore_zone_t;

typedef struct bt_handle bt_handle_if;



#endif // ITL_STRUCTS_IF_H
