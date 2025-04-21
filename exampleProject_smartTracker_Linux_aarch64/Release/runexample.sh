#!/bin/bash

cd ..
PATH="$(pwd)/libs/"
export LD_LIBRARY_PATH=$PATH
cd Release
./exampleProject_smartTracker_Linux_aarch64
