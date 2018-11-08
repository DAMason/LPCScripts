#!/usr/bin/env python3
"""
Bits and pieces needed to deal with voms DN list
"""

import os
import sys

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

import ssl


import xml.etree.ElementTree as ET


from LPCScriptsConfig import *


#

class VOMSTools(urllib2.HTTPSHandler):

    def __init__(self, cert=None, capath=None):

        urllib2.HTTPSHandler.__init__(self)
        self.cert = cert
        self.capath = capath

#    from Robert Illingworth -- prior to v3.6:
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#    and post 3.6 (untested):
#    self.context=ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.context.load_verify_locations(capath=self.capath)
        self.context.load_cert_chain(self.cert)


    def getDNs(self, debug=False):


        queryUrl="https://voms2.cern.ch:8443/voms/cms/services/VOMSCompatibility?method=getGridmapUsers"

        if debug:
            print("Request: %s" % queryUrl)
        try:
            reply = urllib2.urlopen(queryUrl, context=self.context).read().decode('utf8')
        except (urllib2.HTTPError) as err:
            print("Failed to open: %s" % queryUrl)
            print("Error code %i" % err)
            sys.exit(1)
        except (ConnectionRefusedError) as err:
            print("Failed to open: %s" % queryUrl)
            print("Error code %i" % err)
            sys.exit(1)

        replydict=ET.fromstring(reply)

        dnList=[]
        for item in replydict.getiterator():
           if item.tag == 'getGridmapUsersReturn':
              dnList.append(item.text)


        if debug:
             print("Parsed xml:")
             print(dnList)

        return (dnList)

if __name__ == '__main__':

    thingy = VOMSTools(cert="/tmp/x509up_u0", capath="/etc/grid-security/certificates")


    myreply=thingy.getDNs(debug=True)
