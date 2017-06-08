"""Test cases for project"""
import shutil
import os
import logging

class TestCase(object):
    def __init__( self ):
        "initialization"
        self.topo = None
        self.net = None
        self.outputdir = None

    def get_output_dir( self ):
        "return the output directory"
        if self.outputdir != None:
            return self.outputdir
        else:
            dirs = [d for d in os.listdir('../debug/') if d.startswith('log') and os.path.isdir(os.path.join('../debug/', d))]
            maxlog = 0 if len(dirs) == 0 else max([int(n[3:]) for n in dirs])
            newdir = '../debug/log'+str(maxlog + 1)
            os.mkdir(newdir)
            self.outputdir = newdir
            return self.outputdir
        
    def pre_start( self ):
        "do preparement for network start"

    def get_net( self ):
        "return the mininet object or network object here"
        return self.net

    def duration1( self ):
        "the interval between the start of network and do post start action"
        return 1
    
    def post_start( self ):
        "do what you want immediately after the start of the network, or the preparement of your test"

    def duration2( self ):
        "the interval between the finish of post start action and the begin of the test"
        return 1
    
    def test( self ):
        "do test here"

    def duration3( self ):
        "the interval between finish of calling test and do clean task, or the test duration"
        return 10
    
    def clean( self, exception = False ):
        "do clean work, the network will shutdown immediately after this"

    def post_test( self, exception = False ):
        "do extra works after correct executions"
        if exception == False:
            try:
                shutil.copy('../floodlight/target//bin/floodlightdefault.properties', 
                            os.path.join(self.get_output_dir(), 'floodlightdefault.properties'))
                logging.info('floodlightdefault.properties copied')
            except IOError:
                logging.warning('floodlightdefault.properties copy failed, IOError!')

        
