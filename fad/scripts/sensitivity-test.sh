#!/bin/bash
function start_floodlight( )
{
    cd ../floodlight/
    ./floodlight.sh &
    cd ../scripts/
}

function require_root( )
{
    if [[ $EUID -ne 0 ]]; then
		echo "This script must be run as root" 1>&2
		exit 1
    fi
}

# parameters: topo_file, name, logdir
function test_one_topo( )
{
    topo_file=$1
    name=$2
    logid=$3
    runid=$4
    start_floodlight
    sleep 5
    sudo python test.py general tf=$topo_file duration=900
    sleep 10
    logdir=../experiment-data/running/sensitivity/output${runid}/${name}/${logid}
    if [ ! -d ${logdir} ]; then
		mkdir -p ${logdir}
    fi
    mv -T ../debug/log1 ${logdir}
}
function check_output_dir( )                                                                                                                  
{
    if [ -d ../debug/log1 ]; then
		echo output directory 'debug/log1' exists, please empty existed log folders.
		exit 2
    fi
    if [ -d ../experiment-data/running/sensitivity/ ]; then
        echo output directory '../experiment-data/running/sensitivity' exists, please backup your data and remove this folder
		exit 2
    fi       
}

check_output_dir
require_root
topo_dir=../data/selected-topo/
for run in $(seq 1 10); do
    for topo in $(ls ${topo_dir}*.gml.dat); do
		name=${topo:${#topo_dir}:-8}
		test_one_topo $topo $name log1 $run
    done
done

