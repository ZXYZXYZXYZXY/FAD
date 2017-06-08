"""start the data plane and do test"""
import datetime
import time
import subprocess
import argparse
import shutil
import os, signal
import sys
import logging

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI

from testcases.testcase import TestCase
from testcases.lineartest import LinearTest
from testcases.internet2test import Internet2Test
from testcases.generaltest import GeneralTest
from testcases.hijacktest import HijackTest
from testcases.aggregatedflowtest import AggregatedFlowTest

def KeyValuePair(v):
    fields = v.split('=')
    if len(fields) != 2:
        raise argparse.ArgumentTypeError("String must have the format of key=value")
    else:
        return v

def CaseName( v ):
    casenames = ['linear', 'hijack', 'internet2', 'aggregate', 'general']
    for cn in casenames:
        if v.lower() == cn:
            return cn
    raise argparse.ArgumentTypeError("casenames must be in {}".format(casenames))

def AutoSelect( v ):
    casenames = {'auto': True, 'man': False}
    for name,value in casenames.iteritems():
        if v.lower() == name:
            return value
    raise argparse.ArgumentTypeError("autocontroller must be set in {}".format(casenames.keys()))

def get_matrices_from_tf( topo_file ):
    # map from name to matrix
    matrices = {}
    matrix = None
    name = Nonen
    size = None
    with open(topo_file, 'r') as tf:
        for line in tf:
            if line.isspace():
                if name != None:
                    if len(matrix) != size[0]:
                        raise ValueError('the data size is not consistent with the row value in {}'.format(name))
                    matrices[name] = matrix
                    matrix = None
                    name = None
                    size = None
            elif name == None:
                name = line[:-1]
            elif size == None:
                size = [int(i) for i in line.split()]
                matrix = []
            else:
                row = [int(i) for i in line.split()]
                if len(row) != size[0]:
                    raise ValueError('the row size is not consistent with the row value in {}'.format(name))
                matrix.append(row)
    return matrices

def init_logger( ):
    "initalize logger"
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s,%(msecs)d %(name)-8s %(levelname)-4s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename='mininet.log',
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-8s %(levelname)-4s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

def start_floodlight( ):
    cmds = split('java -jar /home/pchui/workspace/fad/floodlight/target/floodlight.jar')
    fl = subprocess.Popen(cmds, cwd='/home/pchui/workspace/fad/floodlight/')

def check_floodlight_stats( ):
    pid = None
    p = subprocess.Popen(['pgrep', '-f', 'java.*floodlight'], stdout=subprocess.PIPE)
    out,err = p.communicate()
    for line in out.splitlines():
        pid = int(line)
    return 'OK' if pid != None else 'FAIL'

def clean_floodlight( test, exception = False ):
    # close floodlight and store log files
    pid = None
    p = subprocess.Popen(['pgrep', '-f', 'java.*floodlight'], stdout=subprocess.PIPE)
    out,err = p.communicate()
    for line in out.splitlines():
        pid = int(line)
    if pid != None:
        os.kill(pid, signal.SIGTERM)
        if exception == False:
            try:
                shutil.move('/tmp/floodlight.log', test.get_output_dir())
                logging.info('floodlight log have been moved to output directory')
            except IOError:
                logging.warning('cannot move /tmp/floodlight.log to output directory!')
            
        else:
            try:
                os.remove('/tmp/floodlight.log')
                logging.info('floodlight log file have been deleted!')
            except OSError:
                logging.warning('unable to delete floodlight log file')
    else:
        logging.warning('cannot find floodlight process, please terminate it manually')


def clean_log( test, exception = False ):
    if exception == False:
        try:
            shutil.move('mininet.log', test.get_output_dir())
            logging.info('mininet.log have been moved to output directory')
        except IOError:
            logging.warning('cannot move mininet.log to output directory!')
            
    else:
        try:
            os.remove('mininet.log')
            logging.info('mininet.log have been deleted!')
        except OSError:
            logging.warning('unable to delete mininet.log')
            
def single_test ( test ):
    exception = False
    net = test.get_net( )
    try:
        test.pre_start( )
        net.start()

        logging.info('do post start task after {} seconds, current: {}'.format( test.duration1(), datetime.datetime.now().strftime('%H:%M:%S.%f') ))
        time.sleep( test.duration1( ) )
        test.post_start( )
        
        logging.info('do test task after {} seconds, current: {}'.format( test.duration2(), datetime.datetime.now().strftime('%H:%M:%S.%f')))
        time.sleep( test.duration2( ) )
        test.test( )

        logging.info('do clean task after {} seconds, current: {}'.format( test.duration3(), datetime.datetime.now().strftime('%H:%M:%S.%f')))
        time.sleep( test.duration3( ) )
        # logging.info('run CLI')
        # CLI( net )
    except:
        e = sys.exc_info()[0]
        logging.error('exception happens: {}'.format(e))
        exception = True
    finally:
        test.clean( exception )
        net.stop()
        if exception:
            subprocess.call(['mn', '-c'])
    clean_floodlight( test, exception )
    clean_log( test, exception )
    test.post_test( exception)
    logging.info('test finished!')

if (__name__ == '__main__'):
    init_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument('casename', metavar='test', type=CaseName, help='the test case name')
    # disable this option
    # parser.add_argument('autocontroller', metavar='autocontroller', type=AutoSelect, default='auto', help='Start floodlight controller manually or automatically: auto = automatically, man = manually') 
    parser.add_argument('arguments', metavar='arguments', type=KeyValuePair, nargs='*', help='the extra arguments delivered to the test case, in the format of key=value')

    args = parser.parse_args()
    params = {}
    for param in args.arguments:
        pair = param.split('=')
        if(len(pair) != 2):
            continue
        else:
            params[pair[0]] = pair[1]

    # disabled
    # if(args.autocontroller):
    #     logging.info('start floodlight...')
    #     start_floodlight( )
    #     time.sleep(5)

    # if check_floodlight_stats( ) == 'FAIL':
    #     logging.error('cannot detect floodlight controller process, exit now!')
    #     sys.exit(1)

    test = None
    if args.casename == 'linear':
        test = LinearTest( **params )
        single_test( test )
    elif args.casename == 'hijack':
        test = HijackTest( **params )
        single_test( test )
    elif args.casename == 'internet2':
        test = Internet2Test( **params )
        single_test( test )
    elif args.casename == 'aggregate':
        test = AggregatedFlowTest( **params )
        single_test( test )
    elif args.casename == 'general':
        topo_file = None
        for name,value in params.iteritems():
            if name == 'tf':
                topo_file = value
                break
        if topo_file == None:
            raise ValueError('parameter tf is required for topology general')
        matrices =  get_matrices_from_tf( topo_file )
        for name, matrix in matrices.iteritems():
            test = GeneralTest(matrix = matrix, **params)
            logging.info('start test for topology {}'.format(name))
            single_test( test )
            logging.info('test for topology {} finished'.format(name))
    else:
        logging.error('cannot find the test case {} in our scripts!'.format(args.casename))
        

