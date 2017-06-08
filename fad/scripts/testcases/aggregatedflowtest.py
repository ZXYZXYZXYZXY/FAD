"""
Test for aggregated flow.
We test aggregated flow with a linear topology, and several host was attached to each edge switch.
Each switch in one edge would send packets to the corresponding another one at the another end of edge.
"""
import time
import logging
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, IVSSwitch, UserSwitch, OVSSwitch
from mininet.cli import CLI

from testcase import TestCase

class AggregatedFlowTestTopo (Topo):
    "linear topology for aggregated flow test"
    def __init__ (self, nodes = 5, hosts = 5):
        Topo.__init__(self)
        sws = []
        self.left_hosts = []
        self.right_hosts = []
        # create switches
        for i in range(nodes):
            sws.append(self.addSwitch('s{}'.format(i+1), protocols='OpenFlow10'))
            if i != 0:
                self.addLink(sws[i-1], sws[i])
        # add hosts
        for i in range(hosts):
            for j in range(nodes):
                # construct left part of hosts
                tmp = self.addHost('h1{}'.format(j+1), ip='10.0.1.{}/16'.format(100+j+1))
                self.left_hosts.append(tmp)
                self.addLink(tmp, sws[0])
                # construct right part of hosts
                tmp = self.addHost('h2{}'.format(j+1), ip='10.0.2.{}/16'.format(100+j+1))
                self.right_hosts.append(tmp)
                self.addLink(tmp, sws[len(sws)-1])
                
    def get_left_hosts( self ):
        "get left part of hosts"
        return self.left_hosts

    def get_right_hosts( self ):
        "get right part of hosts"
        return self.right_hosts
    
class AggregatedFlowTest( TestCase ):
    "test case for aggregated flow"
    def __init__( self, nodes=5, hosts=5, inject = False):
        super(AggregatedFlowTest, self).__init__()
        self.nodes = int(nodes) if not isinstance(nodes, int) else nodes
        self.hosts = int(hosts) if not isinstance(hosts, int) else hosts
        self.topo = AggregatedFlowTestTopo(self.nodes, self.hosts)
        # self.net = Mininet(self.topo, controller=lambda name: RemoteController( name, ip='127.0.0.1', port=6653 ), switch=OVSSwitch)
        self.net = Mininet(self.topo)
        self.left_hosts = self.construct_hosts(self.topo.get_left_hosts())
        self.right_hosts = self.construct_hosts(self.topo.get_right_hosts())
        # ignore construct packet sniffing and anomaly injection
        # this is ONLY a test script, not the final experiment scripts

    def construct_hosts(self, host_names):
        hosts_node = []
        for name in host_names:
            hosts_node.append(self.net.getNodeByName(name))
        return hosts_node

    def post_start( self ):
        # leverage ping to construct the initial flow rule
        for i in range( len(self.left_hosts)):
            self.net.ping([self.left_hosts[i], self.right_hosts[i]])

    def inject_malicious( self ):
        # do nothing
        pass
    
    def test( self ):
        sport = 2000
        dport_start = 3000
        dport_end = 6000
        count = 1000000
        delay = 10000
        dports = '{}-{}'.format(dport_start, dport_end + 1)
        time.sleep(1)
        # destination port is used as the packets count to be sent and the packet identity
        for i in range( len(self.left_hosts) ):
            left_name = self.left_hosts[i].name
            left_ip = self.left_hosts[i].IP()
            right_name = self.right_hosts[i].name
            right_ip = self.right_hosts[i].IP()
            # construct and inject commands
            left_command = './sendpkt -i {}-eth0 -g {} -p {} -w {}us -c {} {} &'.format(left_name, sport, dports, delay, count, right_ip)
            logging.info('send command to {}: {}'.format(left_name, left_command))
            right_command = './sendpkt -i {}-eth0 -g {} -p {} -w {}us -c {} {} &'.format(right_name, sport, dports, delay, count, left_ip)
            logging.info('send command to {}: {}'.format(right_name, right_command))
            self.left_hosts[i].cmd(left_command)
            self.right_hosts[i].cmd(right_command)
        logging.info('traffic injected, last for {} seconds...'.format(count*delay/1000/1000) )

    def duration3( self ):
        return 300

    def clean( self, exception = False ):
        for host in self.left_hosts:
            host.cmd('kill %./sendpkt')
        for host in self.right_hosts:
            host.cmd('kill %./sendpkt')
        time.sleep(3)




        
