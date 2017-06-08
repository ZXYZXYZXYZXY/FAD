#!/bin/bash

scriptname=$0

function usage
{
	cat <<EOF
Usage: $scriptname [-a] [-t] [-?]
    -a run all experiments
    -t run throughput test experiment
    -l run sensitivity test with linear topology
    -L run sensitivity test with linear topology (AggregatedFlow)
    -s run sensitivity test with Simulated rules (SingleFlow)
    -I run sensitivity test with Internet2 rules (AggregatedFlow)
    -B run basic aggregated flow test
    -? show this message
EOF
}

function require_root
{
    if [[ $EUID -ne 0 ]]; then
		echo "This script must be run as root" 1>&2
		exit 1
    fi
}

FADE_CONTROLLER_PATH="../floodlight/floodlight.sh"
COMMON_CONTROLLER_PATH="../floodlight-nofad/floodlight.sh"
FADE_PATH="../floodlight"
FADE_CONFIG_PATH="../floodlight/src/main/resources/floodlightdefault.properties"
compile_status=""
DEFAULT_FADE_MODE="SingleFlow"
function clean_up_compile
{
	if [ ! "${compile_status} " == " " ]; then
		sed -i "s/detectionMode=.*/detectionMode=${DEFAULT_FADE_MODE}/g" ${FADE_CONFIG_PATH}
		echo reset detection mode to ${DEFAULT_FADE_MODE}, please rebuild it manually.
	fi
}

function compile_FADE
{
	current_detection_mode=$(cat ${FADE_CONFIG_PATH} | grep 'detectionMode=' | cut -d '=' -f2)
	target_detection_mode=""
	echo FADE is in ${current_detection_mode} mode
	if [ "$1" == "SingleFlow" -o "$1" == "AggregatedFlow" ]; then
		echo compile FADE into $1 mode
		target_detection_mode=$1
	elif [ ! "$1 " == " " ]; then
		echo cannot build FADE to detection mode $1
		exit 1
	else
		echo skip build FADE
		return
	fi
	if [ ${current_detection_mode} == ${target_detection_mode} ]; then
		echo FADE already in ${target_detection_mode}, skip building
		return
	fi
	
	# rebuild fade
	compile_status="compiling"
	trap clean_up_compile SIGHUP SIGINT SIGTERM
	sed -i "s/detectionMode=.*/detectionMode=${target_detection_mode}/g" ${FADE_CONFIG_PATH}
	cd ${FADE_PATH}
	mvn package -DskipTests
	mvn_status=$?
	if [ ${mvn_status} -ne 0 ]; then
		echo build FADE fail, please check your source code
		exit 1
	fi
	cd -
	echo rebuild FADE into ${target_detection_mode} successfully.
	compile_status=""
	trap - SIGHUP SIGINT SIGTERM
}

function run_throughput_test
{
	max_run=3
	max_topo_len=15
	compile_FADE "SingleFlow"
	echo run throughput test...
	for run in $(seq 1 ${max_run})
	do
		for len in $(seq 3 ${max_topo_len})
		do
			log_dir="../experiment-data/running/throughput/fad/run${run}/log${len}"
			if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
			python test.py -c auto -p ${FADE_CONTROLLER_PATH} -t nodes=${len} -o ${log_dir} linear
			# without fade
			log_dir="../experiment-data/running/throughput/nofad/run${run}/log${len}"
			if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
			python test.py -c auto -p ${COMMON_CONTROLLER_PATH} -t nodes=${len} -o ${log_dir} linear
			# with fade
		done 
	done
	echo throughput test DONE ^_^
}


function run_sensitivity_test_with_linear_topo
{
	max_run=10
	num_of_nodes=(5 5 5 5 5 5 5 5 5 5 5 5)
	num_of_hosts=(40 50 60 70 80 90 100 120 140 160 180 200)
	num_of_injects=(20 20 20 20 30 30 40 40 50 60 70 80)
	compile_FADE "SingleFlow"
	echo run sensitivity test with linear topo
	length=${#num_of_hosts[@]}
	for run in $(seq 1 ${max_run}); do
		for idx in $(seq 0 $((length-1))); do
			nodes=${num_of_nodes[$idx]}
			hosts=${num_of_hosts[$idx]}
			injects=${num_of_injects[$idx]}
			log_dir="../experiment-data/running/sensitivity@linear/node${nodes}_hosts${hosts}_injects${injects}/run${run}/"
			if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
			echo nodes=${nodes}, hosts=${hosts}, injects=${injects}
			python test.py -c auto -p ${FADE_CONTROLLER_PATH} -t nodes=${nodes} fake_hosts=$((hosts-1)) num_of_injects=${injects} duration=300 -o ${log_dir} linear
		done
	done
}

function run_sensitivity_test_with_linear_topo_aggregated_flow
{
	max_run=10
	num_of_nodes=(5 5 5 5 5 5 5 5 5 5 5 5)
	num_of_hosts=(40 50 60 70 80 90 100 120 140 160 180 200)
	num_of_injects=(20 20 20 20 30 30 40 40 50 60 70 80)
	compile_FADE "AggregatedFlow"
	echo run sensitivity test with linear topo
	length=${#num_of_hosts[@]}
	for run in $(seq 1 ${max_run}); do
		for idx in $(seq 0 $((length-1))); do
			nodes=${num_of_nodes[$idx]}
			hosts=${num_of_hosts[$idx]}
			injects=${num_of_injects[$idx]}
			log_dir="../experiment-data/running/sensitivity@linear-aggregated/node${nodes}_hosts${hosts}_injects${injects}/run${run}/"
			if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
			echo nodes=${nodes}, hosts=${hosts}, injects=${injects}
			python test.py -c auto -p ${FADE_CONTROLLER_PATH} -t nodes=${nodes} fake_hosts=$((hosts-1)) num_of_injects=${injects} duration=300 -o ${log_dir} linear
		done
	done
}


function run_sensitivity_test_with_simulated_rules
{
	max_run=10
	topo_dir="../data/selected-topo/"
	compile_FADE "SingleFlow"
	echo run sensitivity test with simulated flow rules...
	for run in $(seq 1 ${max_run}); do
		for topo in $(ls ${topo_dir}*.gml.dat); do
			name=${topo:${#topo_dir}:-8}
			log_dir="../experiment-data/running/sensitivity@simulated/output${run}/${name}/log1/"
			if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
			python test.py -c auto -p ${FADE_CONTROLLER_PATH} -t topo_file=${topo} duration=900 -o ${log_dir} general
		done
	done
	echo sensitivity test with simulated flow rules DONE ^_^
}

function run_sensitivity_test_with_internet2_rules
{
	max_run=10
	topo_file="../data/internet2/internet2.gml.dat"
	host_file="../data/internet2/internet2_host_conf.json"
	rule_file="../data/internet2/internet2_rules.dat"
	compile_FADE "AggregatedFlow"
	echo run sensitivity test with Internet2 flow rules...
	for run in $(seq 1 ${max_run}); do
		log_dir="../experiment-data/running/sensitivity@internet2/output${run}/${name}/log1/"
		if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
		python test.py -c auto -p ${FADE_CONTROLLER_PATH} \
			   -t topo_file=${topo_file} host_file=${host_file} duration=900 rule_file=${rule_file} \
			   -o ${log_dir} generalaggregated
	done
	echo sensitivity test with Internet2 flow rules DONE ^_^
}

function run_basic_aggregated_flow_test
{
	max_run=3
	compile_FADE "AggregatedFlow"
	echo run basic aggregated flow test
	for run in $(seq 1 ${max_run}); do
		log_dir="../experiment-data/running/basic_aggregated_flow/output${run}/"
		if [ ! -d ${log_dir} ]; then mkdir -p ${log_dir}; fi
		python test.py -c auto -p ${FADE_CONTROLLER_PATH} -o ${log_dir} aggregated
	done
}

function all
{
	run_throughput_test
	run_sensitivity_test_with_linear_topo
	run_sensitivity_test_with_linear_topo_aggregated_flow
	run_sensitivity_test_with_simulated_rules
	run_sensitivity_test_with_internet2_rules
	run_basic_aggregated_flow_test
}


# main entry
require_root;
if [ $# -eq 0 ]
then
	usage
else
    while getopts "atlLsIB?" OPTION
    do
		case $OPTION in
			a)    all;;
			t)    run_throughput_test;;
			l)    run_sensitivity_test_with_linear_topo;;
			L)    run_sensitivity_test_with_linear_topo_aggregated_flow;;
			s)    run_sensitivity_test_with_simulated_rules;;
			I)    run_sensitivity_test_with_internet2_rules;;
			B)    run_basic_aggregated_flow_test;;
			?)    usage;;
			*)    usage;;
		esac
    done
    shift $(($OPTIND - 1))
fi

