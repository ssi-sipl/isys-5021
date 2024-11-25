
/**************************************************************************************

      II    N     N     N     N      OOOO      SSSSS     EEEEE    N     N    TTTTTTT
     II    NNN   N     NNN   N    OO    OO    S         E        NNN   N       T
    II    N NN  N     N NN  N    OO    OO    SSSSS     EEE      N NN  N       T
   II    N  NN N     N  NN N    OO    OO        S     E        N  NN N       T
  II    N    NN     N    NN      OOOO      SSSSS     EEEEE    N    NN       T
                         copyright (c) 2017, InnoSenT GmbH
                                 all rights reserved

***************************************************************************************

    filename:			ethernetAPI_if.h
    brief:				API for communication between iSYS 5110 AND_I PC over ethernet
    creation:			24.01.2017
    author:				Sebastian Weidmann

    version:			v1.0
    last edit:          24.01.2017
    last editor:        Sebastian Weidmann
    change:             first release

    version:			v1.1
    last edit:          17.03.2017
    last editor:        Philipp Goetz
    change:             bug fixes

    version:			v1.2
    last edit:          08.05.2018
    last editor:        Johannes Witzgall
    change:             added support for iSYS-5020

***************************************************************************************/

#ifndef ETHERNETAPI_IF_H
#define ETHERNETAPI_IF_H
/**************************************************************************************
  includes
**************************************************************************************/
#include "ethernet_API_basicTypes.h"

/**************************************************************************************
 defines
**************************************************************************************/
#ifdef _WIN32
    #ifdef ETHERNETAPI_LIBRARY
        #define ETHERNET_API_EXPORT __declspec(dllexport)
    #else
        #define ETHERNET_API_EXPORT __declspec(dllimport)
    #endif
#else
    #define ETHERNET_API_EXPORT
#endif

#define ETH_MAX_TARGETS (512)

#ifdef __cplusplus
extern "C" {
#endif

/**************************************************************************************
 typedefs
**************************************************************************************/
typedef enum ETHResult
{
    ETH_ERR_OK                                  = 0x0000,
    ETH_ERR_HANDLE_NOT_INITIALISED              ,
    ETH_ERR_SYSTEM_ALREADY_INITIALISED          ,
    ETH_ERR_SYSTEM_NOT_INITIALISED              ,
    ETH_ERR_CREATE_HANDLE                       ,
    ETH_ERR_NULL_POINTER                        ,
    ETH_ERR_FUNCTION_DEPRECATED                 , // 50
    ETH_ERR_PORT_ALREADY_INITIALISED            ,
    ETH_ERR_PORT_IN_USE                         ,
    ETH_ERR_CONNECTION_CLOSED                   ,
    ETH_ERR_CONNECTION_RESET                    ,
    ETH_ERR_COMMUNICATION_TIMEOUT               ,
    ETH_ERR_COMMUNICATION_ERROR                 ,
    ETH_ERR_CONNECTION_LOST                     ,
    ETH_ERR_TARGET_NOT_ENOUGH_DATA_AVAILABLE    ,
    ETH_ERR_TARGET_DATA_CORRUPTED               ,
    ETH_ERR_TARGET_DATA_SIZE                    ,
    ETH_ERR_RAW_NOT_ENOUGH_DATA_AVAILABLE       ,
    ETH_ERR_RAW_DATA_CORRUPTED                  ,
    ETH_ERR_RAW_DATA_SIZE                       ,
    ETH_ERR_MUTEX_ERROR                         ,
    ETH_ERR_NETWORK_INTERFACE
} ETHResult_t;

typedef enum ETHTargetListError
{
    ETH_TARGET_LIST_OK                          = 0x00,
    ETH_TARGET_LIST_FULL                        = 0x01,
    ETH_TARGET_LIST_ALREADY_REQUESTED           = 0x02,
    ETH_TARGET_LIST_NOT_ACTIVE                  = 0x03,
    ETH_TARGET_LIST_DATA_CORRUPTED              = 0x04
}ETHTargetListError_t;

union ETHTargetListError_u
{
    ETHTargetListError_t ETHTargetListError;
    uint32_t dummy;
};

typedef struct ETHTarget{
    float32_t signalStrength;	/* [dB] */
    float32_t range;			/* [m]*/
    float32_t velocity;         /* [m/s] */
    float32_t angleAzimuth;     /* [°] */
    float32_t reserved1;
    float32_t reserved2;
}ETHTarget_t;

typedef struct ETHTargetList{
    ETHTargetListError_u ETHTargetListError;
    ETHTarget_t targetList[ETH_MAX_TARGETS];
    uint16_t nrOfTargets;
    uint16_t frameID;
}ETHTargetList_t;


typedef struct ETHHandle *ETHHandle_t;

/**************************************************************************************
 api functions
**************************************************************************************/
ETHERNET_API_EXPORT ETHResult_t ETH_initSystem(ETHHandle_t *pHandle, uint8_t ipPart1, uint8_t ipPart2, uint8_t ipPart3, uint8_t ipPart4, uint32_t udpPortNumber);
ETHERNET_API_EXPORT ETHResult_t ETH_exitSystem(ETHHandle_t pHandle);
ETHERNET_API_EXPORT ETHResult_t ETH_getApiVersion(float32_t *version);

/* additional functions */
ETHERNET_API_EXPORT ETHResult_t ETH_getTargetList(ETHHandle_t pHandle, ETHTargetList_t *pTargetList); /* get target list  */


/**************************************************************************************
 api functions end
**************************************************************************************/


#ifdef __cplusplus
}
#endif

#endif // ETHERNETAPI_IF_H























