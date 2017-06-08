#!/bin/bash

function start_nofad_floodlight()
{
    cd ../floodlight-nofad/
    ./floodlight.sh &
    cd ../scripts
}

function start_fad_floodlight()
{
    cd ../floodlight/
    ./floodlight.sh &
    cd ../scripts
}

function check_root()
{
    if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root" 1>&2
	exit 1
    fi
}
function check_output_directory()                                                                                                            
{                                                                                                                  
    if [ -d ../experiment-data/running/throughput/fad ]; then
	echo "output directory 'debug/fad' exists, please backup and remove it"     
	exit 2                                                                                                   
    fi                                                                                                   
    # if [ -d ../experiment-data/running/throughput/nofad ]; then                                                    
    #     echo "output directory 'debug/nofad exists, please backup and remove it"
    #     exit 2 
    # fi
    if [ -d ../debug/log1 ]; then 
        echo "output directory 'debug/log1' exists, please backup and remove it"
        exit 2
    fi
}                                                                                                                                    
check_root;
check_output_directory;  

for run in $(seq 1 3)
do
    for len in $(seq 3 15)
    do
	# without fad
	start_nofad_floodlight;
	sleep 5
	python test.py linear nodes=$len inject=false
	sleep 5
	if [ ! -d ../experiment-data/running/throughput/nofad/run$run/log$len ]
	then
	    mkdir -p ../experiment-data/running/throughput/nofad/run$run/log$len
	fi
	mv -T ../debug/log1 ../experiment-data/running/throughput/nofad/run$run/log$len

	# fad
	start_fad_floodlight;
	sleep 5
	python test.py linear nodes=$len inject=false
	sleep 5
	if [ ! -d ../experiment-data/running/throughput/fad/run$run/log$len ]
	then
	    mkdir -p ../experiment-data/running/throughput/fad/run$run/log$len
	fi
	mv -T ../debug/log1 ../experiment-data/running/throughput/fad/run$run/log$len
    done 
done

