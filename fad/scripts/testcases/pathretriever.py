"""retrieving path from floodlight controller. The communication channel is restful"""

import json
import requests

class PathRetriever( object ):
    def __init__( self, uri='http://127.0.0.1:8080/wm/dumproute/get/json', dpidbase=10):
        "In UserSwitch, the dpidbase should be 10, and in ovs, it should be 16"
        self.uri = uri
        self.dpidbase=dpidbase

    def get_path ( self, srcMac, dstMac ):
        "return the forwarding path only include the outport"
        data = {'src': srcMac, 'dst': dstMac}
        response = requests.post( self.uri, data = json.dumps(data) )
        if response.status_code == 200:
            txt_path = json.loads( response.text )
            path = []
            for node in txt_path:
                path.append( ( int( node['dpid'].replace(':', ''), self.dpidbase ), int(node['port']) ) )
            return path[1::2]
        else:
            return None

    def get_raw_path( self, src_mac, dst_mac):
        "return the forwarding path include both the inport and the outport"
        data = {'src': src_mac, 'dst': dst_mac}
        response = requests.post( self.uri, data = json.dumps(data) )
        if response.status_code == 200:
            txt_path = json.loads( response.text )
            path = []
            for node in txt_path:
                path.append( ( int( node['dpid'].replace(':', ''), self.dpidbase ), int(node['port']) ) )
            return path
        else:
            return None
        
if __name__ == '__main__':
    "test functions"
    retriever = PathRetriever()
    for src in range(1, 6):
        for dst in range(1, 6):
            if src != dst:
                sm = '00:00:00:00:00:0{}'.format(src)
                dm = '00:00:00:00:00:0{}'.format(dst)
                print( retriever.get_path( sm, dm ) )
            
