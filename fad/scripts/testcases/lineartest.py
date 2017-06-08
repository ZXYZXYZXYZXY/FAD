import time
import subprocess
import shlex
import os
import shutil
import logging
import random

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, IVSSwitch, UserSwitch, OVSSwitch
from mininet.nodelib import LinuxBridge
from mininet.cli import CLI

from testcase import TestCase
from pathretriever import PathRetriever

class LinearTopo( Topo ):
    "linear topology with host attaching on edge switches only, using parameter nodes to control the number of switches"
    def __init__( self, nodes = 5):
        Topo.__init__( self )
        sws = []
        if not isinstance(nodes, int):
            nodes = int(nodes)
        for i in range(nodes):
            sws.append(self.addSwitch('s{}'.format(i+1)))
            if(i != 0):
                self.addLink(sws[i-1], sws[i])
        h1 = self.addHost('h1', ip = '10.0.0.1')
        h2 = self.addHost('h2', ip = '10.0.0.2')
        self.addLink(h1, sws[0])
        self.addLink(h2, sws[nodes-1])

class LinearTest( TestCase ):
    "test case for topology LinearTopo"
    "Linear topology, links are displayed following:"
    "h1-eth0<->s1-eth2"
    "h2-eth0<->s5-eth2"
    "s1-eth1<->s2-eth1"
    "s2-eth2<->s3-eth1"
    "s3-eth2<->s4-eth1"
    "s4-eth2<->s5-eth1"

    def __init__( self, nodes=5, inject=False ):
        super(LinearTest, self).__init__()
        self.topo = LinearTopo(nodes)
        self.net = Mininet(self.topo, controller=lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ), switch=OVSSwitch)
        self.h1 = self.net.get('h1')
        self.h2 = self.net.get('h2')
        self.nodes = int(nodes) if not isinstance(nodes, int) else nodes
        self.inject = inject if isinstance(inject, bool) else ('true' == inject.lower())
        self.popens = []
        if str(self.net.switch).find('UserSwitch') != -1:            
            self.path_retriever = PathRetriever(dpidbase=16)
        else:
            self.path_retriever = PathRetriever(dpidbase=10)
        
    def post_start( self ):
        self.net.ping([self.h1, self.h2])
        # disable ICMP messages
        # self.h1.cmd('iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP')
        # self.h2.cmd('iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP')

    def inject_malicious( self ):
        # inject malicious rule to drop traffic from h1 to h2
        path = self.path_retriever.get_path( self.h1.MAC(), self.h2.MAC() )
        if len(path) < 3:
            logging.warning('path shorten than 3, give up malicious injecting')
        else:
            inject_point = path[ random.randint(1, len(path)-2) ]
            sw = None
            outport = None
            for s in self.net.switches:
                if int(s.defaultDpid(), 16) == inject_point[0]:
                    sw = s
            outport = 2 if inject_point[1] == 1 else (inject_point[1] - 1)
            cmd = None
            if str(self.net.switch).find('OVSSwitch') != -1:            
                cmd = 'ovs-ofctl add-flow {} ip,nw_dst={},priority=255,actions=output:{}'.format(sw.name, self.h2.IP(), outport )
            elif str(self.net.switch).find('UserSwitch') != -1:
                cmd = 'dpctl unix:/tmp/{} flow-mod cmd=add,table=0,hard=300,prio=255 eth_type=0x800,ip_dst={} apply:output={}'.format(sw.name, self.h2.IP(), outport )
            else:
                raise ValueError('switch unrecognized! cannot inject malicious rules')
            cmds = shlex.split(cmd)
            subprocess.Popen(cmds)
            logging.info('inject rule finished on switch {}, cmd="{}"'.format(sw.name, cmd))

    def test( self ):
        sport = 2000
        dport_start = 3000
        dport_end = 6000
        count = 1000000
        delay = 10000
        dports = '{}-{}'.format(dport_start, dport_end + 1)
        # self.h1.cmd('tcpdump -w tcpdump-h1.pcap net 10.0.0.0/24 and ip &')
        # self.h2.cmd('tcpdump -w tcpdump-h2.pcap net 10.0.0.0/24 and ip &')
        # for link in self.net.links:
        #     for interface in ( str(link.intf1), str(link.intf2) ):
        #         if interface.startswith('h'):
        #             continue
        #         cmds = shlex.split('tcpdump -i {} -w tcpdump-{}.pcap net 10.0.0.0/24 and ip'.format(interface, interface))
        #         popen = subprocess.Popen(cmds)
        #         self.popens.append(popen)
        time.sleep(1)
        # destination port is used as the packets count to be sent and the packet identity
        logging.info('send command to h1: {}'.format('./sendpkt -i h1-eth0 -g {} -p {} -w {}us -c {} 10.0.0.2 &'.format(sport, dports, delay, count)))
        self.h1.cmd('./sendpkt -i h1-eth0 -g {} -p {} -w {}us -c {} 10.0.0.2 &'.format(sport, dports, delay, count));
        # self.h1.cmd('nping -udp -g {} -p {} -N -delay {} -c 1 10.0.0.2 &'.format(sport, dports, delay))
        self.h2.cmd('./sendpkt -i h2-eth0 -g {} -p {} -w {}us -c {} 10.0.0.1 &'.format(sport, dports, delay, count));
        # self.h2.cmd('nping -udp -g {} -p {} -N -delay {} -c 1 10.0.0.1 &'.format(sport, dports, delay))
        logging.info('traffic injected, last for {} seconds...'.format(count*delay/1000/1000) )
        if self.inject:
            wt = random.randint(10,20)
            logging.info('waiting for {} seconds to inject malicious traffic'.format(wt))
            time.sleep(wt)
            self.inject_malicious()
        time.sleep(30)
        for i in range(6):
            result = self.net.iperf([self.h1, self.h2])
            logging.info('iperf between h1 and h2: ' + str(result))
            time.sleep(10)
        
        
    def duration3( self ):
        return 1
    
    def clean( self, exception = False ):
        # kill all related process
        self.h1.cmd('kill %./sendpkt')
        self.h2.cmd('kill %./sendpkt')
        time.sleep(3)
        self.h1.cmd('kill %tcpdump')
        self.h2.cmd('kill %tcpdump')
        for popen in self.popens:
            popen.terminate()

    def post_test( self, exception = False ):
        super(LinearTest, self).post_test(exception)
        pcaps = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.pcap')]
        for pcap in pcaps:
            if exception == True:
                try:
                    os.remove(pcap)
                    logging.info('pcap file have been deleted!')
                except OSError:
                    logging.warning('Cannot delete pcap files')
            else:
                try:
                    shutil.move(pcap, self.get_output_dir())
                    logging.info('pcap files {} have been moved to output directory'.format(pcap))
                except IOError:
                    logging.warning('cannot move pcap file {} to output directory.'.format(pcap))
