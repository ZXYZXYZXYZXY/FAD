import re, os, sys, collections

def print_err(*args):
    sys.stderr.write(' '.join(map(str,args)) + '\n')
    
def parse_folder( folder_name ):
    "parse the lowest log folder, which should contains mininet.log"
    mnlog_name = os.path.join(folder_name, 'mininet.log')
    if not os.path.isfile(mnlog_name):
        print_err( 'path ' + mnlog_name + ' is not file.' )
        return -1
    iperf_rex = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}\W[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]+\Wroot\W*INFO\Wiperf\Wbetween\W(\w+)\Wand\W(\w+):\W*\[\'([0-9\.]+)\W*(K|M|G)bits\/sec\',\W*\'([0-9\.]+)\W*(K|M|G)bits\/sec\'\]')
    
    iperf_result = collections.defaultdict( list )
    conversion_map = {'K': 1.0/1024/1024, 'M': 1.0/1024, 'G': 1}
    with open(mnlog_name, 'r') as mnlog:
        for line in mnlog:
            m = re.search(iperf_rex, line)
            if m != None:
                src = m.group(1)
                dst = m.group(2)
                rate1 = float(m.group(3)) * conversion_map[m.group(4)]
                rate2 = float(m.group(5)) * conversion_map[m.group(6)]
                iperf_result[(src, dst)].append( (rate1, rate2) )
    return iperf_result

if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isdir( sys.argv[1] ):
        print_err('usage: ' + sys.argv[0] + ' logdir')
        sys.exit(2)
    nofad = os.path.join(sys.argv[1], 'nofad')
    fad = os.path.join(sys.argv[1], 'fad')
    if not os.path.isdir( nofad ) or not os.path.isdir( fad ):
        print_err('logdir should contain two subdirectories: "fad" and "nofad"')
        sys.exit(2)

    results = {}
    for opt in ['nofad', 'fad']:
        toplevel = os.path.join(sys.argv[1], opt)
        rundir = [os.path.join(toplevel,d) for d in os.listdir(toplevel) if d.startswith('run') and os.path.isdir(os.path.join(toplevel, d))]
        for run in rundir:
            run_id = int(run[ run.rfind('run') + 3 : ])
            logdir = [os.path.join( run, d ) for d in os.listdir( run ) if d.startswith('log') and os.path.isdir(os.path.join( run, d))]
            for ld in logdir:
                log_id = int(ld[ld.rfind('log')+3:])
                iperf_result = parse_folder( ld )
                if not results.has_key( opt ):
                    results[opt] = {}
                if not results[opt].has_key( log_id ):
                    results[opt][log_id] = iperf_result
                else:
                    for host_pair, values in iperf_result.items():
                        results[opt][log_id][host_pair].extend(values)
    
    # the final process
    print 'length avg-nofad avg-fad nofad... fad...'
    nofad_res = results['nofad']
    fad_res = results['fad']
    final_res = []
    for length, iperf_map in nofad_res.items():                                                      
        fad_map = fad_res[length]
        if len(iperf_map) != 1 or len(fad_map) != 1:
            print_err(' log file error, we only collect iperf result from one pair of hosts')
            sys.exit(3)
        for hp, pairs in iperf_map.items():
            array1 = []
            array2 = []
            avg1 = 0.0
            avg2 = 0.0
            for p in pairs:                                                
                array1.append(p[0])
                array1.append(p[1])
            avg1 = sum(array1) / len(array1)
            for p in fad_map[hp]:
                array2.append(p[0])
                array2.append(p[1])
            avg2 = sum(array2) / len(array2)
            print length,
            print avg1,
            print avg2,
            for d in array1:
                print d,
            for d in array2:
                print d,
            print
            final_res.append((avg1, avg2))
    
    deviations = [abs(avg1-avg2)/max(avg1,avg2)*100 for (avg1, avg2) in final_res]
    print '\n\n-------------------------- final avg -------------------------------'
    print 'Avg deviation: {}, max deviation: {}'.format(sum(deviations)/len(deviations), max(deviations))
