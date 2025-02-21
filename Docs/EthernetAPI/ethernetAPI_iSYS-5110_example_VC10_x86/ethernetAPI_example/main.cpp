/**************************************************************************************

      II    N     N     N     N      OOOO      SSSSS     EEEEE    N     N    TTTTTTT
     II    NNN   N     NNN   N    OO    OO    S         E        NNN   N       T
    II    N NN  N     N NN  N    OO    OO    SSSSS     EEE      N NN  N       T
   II    N  NN N     N  NN N    OO    OO        S     E        N  NN N       T
  II    N    NN     N    NN      OOOO      SSSSS     EEEEE    N    NN       T
                         copyright (c) 2017, InnoSenT GmbH
                                 all rights reserved

***************************************************************************************

    filename:			main.cpp
    brief:				ethernetAPI example project - reading targetlist from iSYS-5110
    creation:			22.02.2017
    author:				Thomas Popp

    version:			v1.0
    last edit:          ...
    last editor:        ...
    change:				...
    compile switches:	...

***************************************************************************************/


/**************************************************************************************
  includes
**************************************************************************************/
#include <Windows.h>
#include <conio.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include "ethernetAPI_if.h"
#include <fstream>
#include <direct.h>
#include <stdlib.h>


/**************************************************************************************
   local function prototypes
**************************************************************************************/
static void getTargetWithHighestSignal(ETHTargetList_t *pInTargetList, ETHTarget_t *pOutTarget);


/**************************************************************************************
	function name:		main
	purpose:			this function initalizes the Eternet API and reads iSYS-5110 
						target lists of a connected device

	return value:		0=OK, other exit with error
	input parameters:	none
	output parameters:	none

	author:				Thomas Popp
	creation:			22.02.2017
**************************************************************************************/
int main(void)
{
	ETHHandle_t pHandle;
	ETHResult_t res;
	float32_t version;
	uint16_t i;
	ETHTargetList_t pTargetList;
	ETHTarget_t targetHighestSignal;

	/* set IP address and UDP port with iSYS-5110 delivery setting */
	uint8_t ipPart1 = 192;
	uint8_t ipPart2 = 168;
	uint8_t ipPart3 = 60;
	uint8_t ipPart4 = 20;
	uint32_t udpPort = 2050;

	/* read API version*/
	res = ETH_getApiVersion(&version);
	if(res != ETH_ERR_OK){
		std::cout << "---------------------------------\n";
		std::cout << "    ETH_getApiVersion failed\n";
		std::cout << "---------------------------------\n";
		return 1;
	}

	std::cout << "---------------------------------\n";
	std::cout << "    ethernetAPI Version: " << version <<"\n";
	std::cout << "---------------------------------\n";


	/* init iSYS-5110 RADAR sensor */
	res = ETH_initSystem(&pHandle, ipPart1, ipPart2, ipPart3, ipPart4, udpPort);
	if(res != ETH_ERR_OK){
		std::cout << "---------------------------------\n";
		std::cout << "    ETH_initSystem failed\n";
		std::cout << "---------------------------------\n";
		return 2;
	}

	/* read successive target-lists */
	std::cout << "---------------------------------\n";
	std::cout << "FrameID, NrOfTargets, Angle, Range, Velocity, Signal\n";
	std::cout << "---------------------------------\n";

	for(i=0;i<500;i++){
		res = ETH_getTargetList(pHandle, &pTargetList);
		if(res != ETH_ERR_OK){
			std::cout << "---------------------------------\n";
			std::cout << "    ETH_getTargetList failed\n";
			std::cout << "---------------------------------\n";
			res = ETH_exitSystem(pHandle);
			return 3;
		}

		switch(pTargetList.ETHTargetListError.ETHTargetListError){
		case ETH_TARGET_LIST_OK:{
			getTargetWithHighestSignal(&pTargetList, &targetHighestSignal);
			std::cout << pTargetList.frameID << ",\t " << pTargetList.nrOfTargets <<",\t";
			std::cout << targetHighestSignal.angleAzimuth << ",\t" << targetHighestSignal.range <<",\t";
			std::cout << targetHighestSignal.velocity << ",\t" << targetHighestSignal.signalStrength << "\n";
			break;
			}
		case ETH_TARGET_LIST_FULL:{
			getTargetWithHighestSignal(&pTargetList, &targetHighestSignal);
			std::cout << pTargetList.frameID << ",\t" << pTargetList.nrOfTargets <<",\t";
			std::cout << targetHighestSignal.angleAzimuth << ",\t" << targetHighestSignal.range <<",\t";
			std::cout << targetHighestSignal.velocity << ",\t" << targetHighestSignal.signalStrength << "\n";
			std::cout << "    target list full - more targets than maximum number of targets available\n";
			break;
		}
		case ETH_TARGET_LIST_ALREADY_REQUESTED:{
			/* target list already requested - wait then request new target list */
			Sleep(10);
			continue;
		}
		case ETH_TARGET_LIST_NOT_ACTIVE:{
			std::cout << "    target list not active - no device running or connected\n";
			break;
		}
		case ETH_TARGET_LIST_DATA_CORRUPTED:{
			std::cout << "    target list data corrupted - checksum error\n";
			break;
		}
		}

	}

	/* exit iSYS-5110 RADAR sensor */
	res = ETH_exitSystem(pHandle);
	if(res != ETH_ERR_OK){
		std::cout << "---------------------------------\n";
		std::cout << "    ETH_exitSystem failed\n";
		std::cout << "---------------------------------\n";
		return 4;
	}

	std:system("pause");

	return 0;
}


/**************************************************************************************
	function name:		getTargetWithHighestSignal
	purpose:			this function searches the target with the highest signal in a
						target list

	return value:		none
	input parameters:	ETHTargetList_t
	output parameters:	ETHTarget_t

	author:				Thomas Popp
	creation:			22.02.2017
**************************************************************************************/
static void getTargetWithHighestSignal(ETHTargetList_t *pInTargetList, ETHTarget_t *pOutTarget)
{
	uint16_t i;
	uint16_t indexMaxSignal = 0;
	float32_t maxSignal = 0.0f;

	/* return target with zeros, if no target available */
	if(pInTargetList->nrOfTargets == 0){
		pOutTarget->angleAzimuth = 0.0f;
		pOutTarget->range = 0.0f;
		pOutTarget->signalStrength = 0.0f;
		pOutTarget->velocity = 0.0f;
		return;
	}

	/* search target with highest signal */
	for(i=0;i<pInTargetList->nrOfTargets;i++){
		if(pInTargetList->targetList[i].signalStrength > maxSignal){
			indexMaxSignal = i;
			maxSignal = pInTargetList->targetList[i].signalStrength;
		}
	}

	pOutTarget->angleAzimuth	= pInTargetList->targetList[indexMaxSignal].angleAzimuth;
	pOutTarget->range			= pInTargetList->targetList[indexMaxSignal].range;
	pOutTarget->signalStrength	= pInTargetList->targetList[indexMaxSignal].signalStrength;
	pOutTarget->velocity		= pInTargetList->targetList[indexMaxSignal].velocity;
}


/*************************************************************************************/
