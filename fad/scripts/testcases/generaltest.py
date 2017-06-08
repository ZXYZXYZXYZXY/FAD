import time
import subprocess
import shlex
import shutil
import random
import math
import datetime
import os
import logging

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, IVSSwitch, UserSwitch, OVSSwitch
from mininet.nodelib import LinuxBridge
from mininet.cli import CLI

from testcase import TestCase
from pathretriever import PathRetriever

class GeneralTest( TestCase ):
    "A general test case which is based on customized topology build from adjacent matrix, and can randomly inject malicious rules"
    def __init__( self, matrix=None, duration=360, **kwargs):
        "initialization"
        super(GeneralTest, self).__init__( )
        self.matrix = matrix
        self.duration = duration if isinstance(duration, int) else int(duration)
        # validate the matrix
        if self.matrix == None:
            raise ValueError('parameter matrix cannot be none.')
        matrix_len = len(matrix)
        for row in matrix:
            if matrix_len != len(row):
                raise ValueError('parameter matrix is illegal.')
            for val in row:
                if val != 0 and val != 1:
                    raise ValueError('parameter matrix is illegal.')
        # initialization
        self.net = Mininet(controller=lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ), switch=OVSSwitch)
        self.net.addController('c0')
        # add switches, hosts and links between host and switch
        for i in range(1, len(self.matrix)+1):
            h = self.net.addHost('h{}'.format(i), ip='10.{}.{}.1'.format(i/255, i%255))
            s = self.net.addSwitch('s{}'.format(i), dpid=str(i), protocols='OpenFlow10')
            self.net.addLink(h, s)
        # add links between switches
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix)):
                if matrix[i][j] == 1:
                    s1 = self.net.get('s{}'.format(i+1))
                    s2 = self.net.get('s{}'.format(j+1))
                    self.net.addLink(s1, s2)
        if str(self.net.switch).find('UserSwitch') != -1:            
            self.path_retriever = PathRetriever(dpidbase=16)
        else:
            self.path_retriever = PathRetriever(dpidbase=10)
        self.inject_percent = [0.4, 0.5]
        self.inject_count = None

        
    def post_start( self ):
        "do what you want immediately after the start of the network, or the preparement of your test"
        self.net.pingAll()
        
    def duration2( self ):
        "the interval between the finish of post start action and the begin of the test"
        return 10

    def inject_malicious_rules( self ):
        "inject malicious rules"
        # initialze essential variables
        hosts = []
        dpid2sw = {}
        for h in self.net.hosts:
            hosts.append( h )
        for sw in self.net.switches:
            dpid2sw[int(sw.defaultDpid(), 16)] = sw

        # retrieve paths
        percent = random.uniform( *self.inject_percent )
        random.shuffle( hosts )
        count = math.ceil( len( hosts ) * percent )
        count = len(hosts) if count > len(hosts) else int(count)
        dst_sel = hosts[:count]
        inject_points = []
        for dst in dst_sel:
            run = 0
            while run < len( hosts ):
                run += 1
                src = random.choice( hosts )
                if src != dst:
                    logging.info('select src: {}, dst: {}'.format(src, dst))
                    path = self.path_retriever.get_path( src.MAC(), dst.MAC() )
                    logging.info('path retrieved: {}'.format(path))
                    if len(path) >= 3:
                        inject_point = path[ random.randint( 1, len(path)-2 ) ]
                        print('inject points: '+ str(inject_point))
                        sw = dpid2sw[ inject_point[0] ]
                        if sw != None:
                            sw_name = sw.name
                            outport = 2 if inject_point[1] == 1 else (inject_point[1] - 1)
                            inject_points.append( (dst.IP(), sw_name, outport ) )
                            break

        inject_points = inject_points[:4]
        self.inject_count = len(inject_points)
        # build inject commands
        inject_cmd = []
        for dst, sw_name, outport in inject_points:
            if str(self.net.switch).find('OVSSwitch') != -1:            
                cmd = 'ovs-ofctl add-flow {} ip,nw_dst={},priority=255,actions=output:{}'.format(sw_name, dst, outport )
                logging.info('inject rule on switch {}, cmd="{}"'.format(sw_name, cmd))
            elif str(self.net.switch).find('UserSwitch') != -1:
                cmd = 'dpctl unix:/tmp/{} flow-mod cmd=add,table=0,prio=255 eth_type=0x800,ip_dst={} apply:output={}'.format(
                    sw_name, dst, outport )
                logging.info('inject rule on switch {}, cmd="{}"'.format(sw_name, cmd))
            else:
                raise ValueError('switch unrecognized! cannot inject malicious rules')
            inject_cmd.append(cmd)
        # inject malicious flows
        for cmd in inject_cmd:
            cmds = shlex.split(cmd)
            subprocess.Popen(cmds)
        logging.info('malicious rule injected finished, current: {}'.format( datetime.datetime.now().strftime('%H:%M:%S.%f') ))
        
    def test( self ):
        "do test here"
        sport = 2000
        dport_start = 3000
        dport_end = 5000
        count = 1000000
        delay = 10000
        dports = '{}-{}'.format(dport_start, dport_end)
        for src in self.net.hosts:
            dsts = ''
            for dst in self.net.hosts:
                if src != dst:
                    dsts += (' ' + dst.IP())
            src.cmd('./sendpkt -i {}-eth0 -g {} -p {} -w {}us -c {} {} &'.format(src.name, sport, dports, delay, count, dsts));
        logging.info('traffic injected for every pair of hosts, last for {} seconds...'.format(count*delay/1000/1000) )

        random.seed(datetime.datetime.now())
        intval = random.randint(5, 20)
        logging.info('inject malicious flow rules after {} seconds...'.format(intval))
        time.sleep(intval)
        self.inject_malicious_rules( )
        # CLI(self.net)

    def duration3( self ):
        "the interval between finish of calling test and do clean task, or the test duration"
        return self.duration
        #return max([360, self.inject_count*150])
    
    def clean( self, exception = False ):
        "do clean work, the network will shutdown immediately after this"
        super(GeneralTest, self).clean(exception)
        for host in self.net.hosts:
            host.cmd('kill %./sendpkt')

    def post_test( self, exception = False):
        super( GeneralTest, self ).post_test (exception)
        if exception == False:
            try:
                shutil.copy('./testcases/generaltest.py', os.path.join(self.get_output_dir(), 'generaltest.py'))
                logging.info('test script "generaltest.py" have been copied to output directory')
            except IOError:
                logging.warning('cannot copy test script "generaltest.py"')


