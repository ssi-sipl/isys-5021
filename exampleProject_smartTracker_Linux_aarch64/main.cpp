#include "include/itl_if.h"
#include "include/ethernetAPI_if.h"
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <unistd.h>
#include <cstring>

int main(int argc, char *argv[])
{

    /* variables for example project */
    ETHHandle_t pETHHandle = NULL;
    ETHResult_t result_eth;
    ITLResult_t result_bt;

    float32_it cycleTime = 0.1f;
    float32_it version;

    bt_target_list_rv_t sensorTargetList[BT_MAX_NR_OF_TARGETS];
    bt_ext_track_list_t trackList[BT_MAX_NR_OF_TRACKS];

    ETHTargetList_t pTargetList;

    uint16_it nrOfTracks;

    result_bt = itl_init_tracker(cycleTime);
    if (result_bt != ITL_OK)
    {
        //ERROR
        std::cout << "Can't initialize tracker handle."<< std::endl;
        return 1;
    }

    result_bt = itl_set_default_values(ITL_PRODUCT_iSYS5021);
    if (result_bt != ITL_OK)
    {
        //ERROR
        std::cout << "Can't set default values."<< std::endl;
        return 1;
    }

    result_bt = itl_set_installation_height(3.0f);
    if (result_bt != ITL_OK)
    {
        //ERROR
        std::cout << "Can't set installation height."<< std::endl;
        return 1;
    }

    result_bt = itl_set_installation_angle(0.0f);
    if (result_bt != ITL_OK)
    {
        //ERROR
        std::cout << "Can't set installation angle."<< std::endl;
        return 1;
    }


    /* initialize targetlist interface (ethernet) */
    if(ETH_getApiVersion(&version) EQUALS_NOT_I ETH_ERR_OK){
        std::cout << "ETH_getApiVersion failed"<< std::endl;
        return 1;
    }
    else{
        std::cout << "ETH_getApiVersion - " << version << std::endl; //QString::number(version, 'f', 4);
    }

    result_eth = ETH_initSystem(&pETHHandle,192,168,252,10,2050);
    if(result_eth EQUALS_NOT_I ETH_ERR_OK){
        std::cout << "ETH_initSystem - failed"<< std::endl;
        return 1;
    }
    else{
        std::cout << "ETH_initSystem - successful"<< std::endl;
    }



    /* read target list */
    while (1){
        do{
            if(ETH_getTargetList(pETHHandle, &pTargetList) EQUALS_NOT_I ETH_ERR_OK){
                  std::cout << "ETH_getTargetList - failed"<< std::endl;
            }
            usleep(50000);
        }while(pTargetList.ETHTargetListError.ETHTargetListError EQUALS_I ETH_TARGET_LIST_ALREADY_REQUESTED);


        if(pTargetList.ETHTargetListError.ETHTargetListError EQUALS_NOT_I ETH_TARGET_LIST_OK){
            std::cout << "ETH_getTargetList - failed"<< std::endl;// << " run number: " << QString::number(i);
        }
        else{
            std::cout << "ETH_getTargetList - successful;  Nr. of Targets:  " << pTargetList.nrOfTargets<< std::endl;
        }

        /* reset target list first */
        memset(sensorTargetList,0,sizeof(bt_target_list_rv_t)*BT_MAX_NR_OF_TARGETS);

        /* convert EthernetAPI Targetlist to Tracker Targetlist*/
        for (int i = 0; i < pTargetList.nrOfTargets; i++){
            if (i == 256){break;}

            sensorTargetList[i].f32_angleAzimuth_deg = pTargetList.targetList[i].angleAzimuth;
            sensorTargetList[i].f32_range_m = pTargetList.targetList[i].range;
            sensorTargetList[i].f32_reserved1 = pTargetList.targetList[i].reserved1;
            sensorTargetList[i].f32_reserved2 = pTargetList.targetList[i].reserved2;
            sensorTargetList[i].f32_rcs_m2 = pTargetList.targetList[i].signalStrength;
            sensorTargetList[i].f32_velocity_mps = pTargetList.targetList[i].velocity;
        }

        /**************************************/
        /******* call tracker execute *********/
        /**************************************/

        result_bt = itl_execute_tracker(sensorTargetList,pTargetList.nrOfTargets);

        if(result_bt EQUALS_NOT_I ITL_OK){
            std::cout << "Can't execute tracker."<< std::endl;
            return -1;
        }

        /**************************************/
        /******* request tracker list *********/
        /**************************************/
        result_bt = itl_receive_track_list(trackList,&nrOfTracks);

        if(result_bt EQUALS_NOT_I ITL_OK){
            std::cout << "Can't get tracker list." << std::endl;
            return -1;
        }

        if(nrOfTracks > 0u){
            printf("Number of active tracks: %i\n",nrOfTracks);
            for(int trackIndex=0;trackIndex<nrOfTracks;trackIndex++){
                printf("Track ID: %i - ",trackList[trackIndex].ui32_objectID);
                printf("Pos X: %f - ",trackList[trackIndex].f32_positionX_m);
                printf("Pos Y: %f - ",trackList[trackIndex].f32_positionY_m);
                printf("Vel X: %f - ",trackList[trackIndex].f32_velocityX_mps);
                printf("Vel Y: %f - ",trackList[trackIndex].f32_velocityY_mps);
                printf("Dir X: %f - ",trackList[trackIndex].f32_directionX);
                printf("Dir Y: %f - ",trackList[trackIndex].f32_directionY);
                printf("Quality: %f \n",trackList[trackIndex].f32_trackQuality);
            }
            printf("----------------------------------------------\n");
        }
    }

    /* exit ethernet handle */
    if(pETHHandle EQUALS_NOT_I NULL_I){
        if(ETH_exitSystem(pETHHandle) EQUALS_NOT_I ETH_ERR_OK){
            std::cout << "ETH_exitSystem - failed"<< std::endl;
        }
        else{
            std::cout << "ETH_exitSystem - successful" << std::endl;
        }
        pETHHandle = NULL_I;
    }
    return 0;
}
