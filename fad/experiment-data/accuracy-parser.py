import re, os, sys, collections, numpy

def print_err(*args):
    sys.stderr.write(' '.join(map(str,args)) + '\n')

def calculate_duration_from_strs( start_str, end_str ):
    time_rex = re.compile('[0-9]{4}\-[0-9]{2}\-([0-9]{2})\W([0-9]{2}):([0-9]{2}):([0-9]{2}),([0-9]+)')
    m1 = re.search(time_rex, start_str)
    m2 = re.search(time_rex, end_str)
    if not m1 or not m2:
        print_err( 'broken time format: {} or {}...'.format(start_str, end_str) )
        sys.exit(1)
    sec = ( int(m2.group(4)) - int(m1.group(4)) )
    sec += ( int(m2.group(3)) - int(m1.group(3)) ) * 60
    sec += ( int(m2.group(2)) - int(m1.group(2)) ) * 60 * 60
    sec += ( int(m2.group(1)) - int(m1.group(1)) ) * 60 * 60 * 24
    usec = int(m2.group(5)) - int(m1.group(5))
    if usec < 0:
        sec -= 1
        usec += 1000000
    dsec = sec + usec/1000000.0
    return dsec

def parse_folder( folder_name ):
    "parse the lowest log folder, which should contains floodlight.log and mininet.log, the second parameter is used to determine the base of dpid value(hex or dec) "
    topo_name = os.path.basename( folder_name[:(folder_name.find('log')-1)])
    fllog_name = os.path.join(folder_name, 'floodlight.log')
    mnlog_name = os.path.join(folder_name, 'mininet.log')
    if not os.path.isfile(fllog_name) or not os.path.isfile(mnlog_name):
        print_err( 'path ' + fllog_name + ' or ' + mnlog_name + ' is not file.' )
        return -1
    detect_rex = re.compile('([0-9]{4}\-[0-9]{2}\-[0-9]{2}\W[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]+)\WERROR\W\[.*\]\W\[FADEController.java:[0-9]+\]\Wfind\Wanomaly\Win\Wrule\WFlowRuleNode\{datapathId=00:00:00:00:00:00:00:([0-9a-fA-F]{2}),.*ipv4_dst=([0-9\.]+(\/[0-9]+)?).*')
    inject_rex = re.compile('([0-9]{4}\-[0-9]{2}\-[0-9]{2}\W[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]+)\Wroot\W+INFO\Winject\Wrule\Won\Wswitch\Ws([0-9]+),\W.*((ip)|(nw))_dst=([0-9\.]+(\/[0-9]+)?).*')
    checking_rex = re.compile('.*constraint.*was\Wevaluated,\Wresult\Wis\W(true|false)')

    anomaly_detect = collections.defaultdict( list )
    anomaly_inject = {}
    checking = 0
    with open(fllog_name, 'r') as fllog:
        for line in fllog:
            m = re.search(detect_rex, line)
            if m != None:
                time_str = m.group(1)
                dpid = int(m.group(2), 10)
                dst = m.group(3)
                anomaly_detect[(dst, dpid)].append(time_str)
            m = re.search(checking_rex, line)
            if m != None:
                checking += 1

    with open(mnlog_name, 'r') as mnlog:
        for line in mnlog:
            m = re.search(inject_rex, line)
            if m != None:
                time_str = m.group(1)
                dpid = int(m.group(2))
                dst = m.group(6)
                anomaly_inject[(dst, dpid)] = time_str

    fn = 0 # false negative
    for key in anomaly_inject.keys():
        if not anomaly_detect.has_key( key ):
            fn += 1
    if fn != 0:
        print_err( 'False negative of {}: '.format( topo_name ) )
        msg = '    ';
        for key in anomaly_inject.keys():
            if not anomaly_detect.has_key( key ):
                msg += (key[0] + ':' + str(key[1]) + ' ' )
        print_err(msg)
    fp = 0
    tp = 0
    dsec = -1.0
    timecost = collections.defaultdict( list )
    for dst, dpid in anomaly_detect.keys():
        if anomaly_inject.has_key( (dst, dpid) ):
            start_str = anomaly_inject[(dst, dpid)]
            tp += 1
            for end_str in anomaly_detect[(dst, dpid)]:
                dsec = calculate_duration_from_strs(start_str, end_str)
                timecost[(dst, dpid)].append( dsec )
        else:
            fp += 1
    if fp != 0:
        print_err( 'False positive {}: '.format(topo_name) )
        msg = '    '
        for key in anomaly_detect.keys():
            if not anomaly_inject.has_key(key):
                msg += (key[0] +':'+str(key[1])+' ')
        print_err( msg )
    stats = (tp, checking-tp-fp, fp, fn) # TP, TN, FP, FN
    return {'sensitivity': stats, 'timecost': timecost}

def parse_run( folder_name ):
    name_results = {}
    topos = [os.path.join(folder_name, d) for d in os.listdir(folder_name)]
    for topo in topos:
        name = os.path.basename( topo )
        logdirs = [os.path.join(topo, d) for d in os.listdir(topo) if d.startswith('log') and os.path.isdir(os.path.join(topo, d))]
        sensitivity = [0, 0, 0, 0] # TP, TN, FP, FN
        timecost = collections.defaultdict( list )
        for logdir in logdirs:
            logid = int(os.path.basename( logdir )[3:])
            result = parse_folder( logdir )
            if result == -1:
                print_err(' cannot parse folder {}'.format(logdir))
                sys.exit(1)
            for i in range(4):
                sensitivity[i] += result['sensitivity'][i]
            for pair, costs in result['timecost'].items():
                timecost[pair].extend(costs)
        name_results[name] = (sensitivity, timecost)
    return name_results

def print_run_result( name_results, order_map = None ):
    # gen output of timecost
    name_results = name_results.items() if order_map == None else sorted(name_results.items(), key=lambda k:order_map[k[0]])
    print 'name min avg max raw_data'
    for name, results in name_results:
        print name,
        raw_data = []
        for pair, result in results[1].items():
            raw_data.extend(result)
        if len(raw_data) == 0:
            print 'no data for {}'.format(name)
            continue
        print min(raw_data),
        print sum(raw_data)/len(raw_data),
        print max(raw_data),
        for data in raw_data:
            print data,
        print
    print
    # gen output for sensitivity
    print 'name FPR FNR'
    for name,results in name_results:
        print name,
        sensitivity = results[0]
        print ('0/0' if sensitivity[1] + sensitivity[2] == 0 else float(sensitivity[2])/(sensitivity[1]+sensitivity[2])),
        print ('0/0' if sensitivity[0] + sensitivity[3] == 0 else float(sensitivity[3])/(sensitivity[0]+sensitivity[3]))
        
if __name__ == '__main__':
    orderfile=None
    if len(sys.argv) == 2 or len(sys.argv) == 3:
        orderfile = '../data/selected-topo/selected-topo.dat' if (len(sys.argv) == 2 or not os.path.isfile(sys.argv[2])) else sys.argv[2]
        if not os.path.isdir( sys.argv[1] ):
            print_err('usage: ' + sys.argv[0] + ' logdir [ orderfile ]')
            sys.exit(2)
    else:
        print_err('usage: ' + sys.argv[0] + ' logdir [ orderfile ]')
        sys.exit(2)
    # gen order map
    order_map = {}
    if orderfile != None:
        orderlines = None
        names = set()
        if len(os.listdir(sys.argv[1])) == 0:
            print_err( 'empty folder, exit...' )
            sys.exit(3)
        names = os.listdir(os.path.join(sys.argv[1], os.listdir(sys.argv[1])[0]))
        with open(orderfile, 'r') as of:
            i=1
            for line in of.readlines():
                for name in names:
                    if line.find(name) != -1:
                        order_map[name] = i
                        i+=1

    runs = [os.path.join(sys.argv[1], d) for d in os.listdir(sys.argv[1]) if os.path.isdir(os.path.join(sys.argv[1],d))]
    results = {}
    for run in runs:
        print '=============== {} ==========='.format(os.path.basename(run if not run.endswith('/') else run[:-1]))
        name_results = parse_run( run )
        # print_run_result( name_results, order_map )
        for name, res in name_results.items():
            tmp = results[name] if name in results else [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, []]
            sensitivity = res[0]
            if sensitivity[1] + sensitivity[2] == 0 or sensitivity[0] + sensitivity[3] == 0:
                continue
            fpr = float(sensitivity[2])/(sensitivity[1]+sensitivity[2])
            fnr = float(sensitivity[3])/(sensitivity[0]+sensitivity[3])
            tmp[0] += fpr
            tmp[1] += fnr
            raw_data = []
            for pair, result in res[1].items():
                raw_data.append(min(result))
            if len(raw_data) == 0:
                print 'finding no result in run {}'.format(run)
                continue
            # print raw_data
            time_min = min(raw_data)
            time_avg = sum(raw_data)/len(raw_data)
            time_max = max(raw_data)
            time_median = numpy.median(raw_data)
            tmp[2] += time_min
            tmp[3] += time_avg
            tmp[4] += time_max
            tmp[5] += time_median
            tmp[6].extend(raw_data)
            results[name] = tmp
    for name, vals in results.items():
        for i in range(len(vals)):
            if isinstance(vals[i], float):
                vals[i] /= len(runs)
            
    if len(order_map) != 0:
        results = sorted(results.items(), key=lambda k:order_map[k[0]])
    else:
        results = results.items()
    # gen output of timecost
    print ('============ Average Value =============')
    print 'name min avg max raw'
    for name, vals in results:
        print '{} {} {} {} {} {}'.format(name, vals[2], vals[3], vals[4], vals[5], vals[6])
    print 
    # gen output for sensitivity
    print 'name FPR FNR'
    for name,vals in results:
        print '{} {} {}'.format(name, vals[0], vals[1])
        
                
