#!/usr/bin/env python3
"""
Bits and pieces needed to deal with voms DN list
"""

import os
import sys
import logging

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

import ssl


import xml.etree.ElementTree as ET


from LPCScriptsConfig import *


# Setting up logging and the SSL context -- In testing found we can use a host cert
# to interact with the CERN VOMS server.

class VOMSTools(urllib2.HTTPSHandler):

    def __init__(self, cert=None, capath=None, debug=False, logobj=None):

        urllib2.HTTPSHandler.__init__(self)
        self.cert = cert
        self.capath = capath
        self.debug = debug


# if given a logger use it, otherwise set one up

        if logobj is not None and isinstance(logobj,logging.getLoggerClass()):
            self.logger=logobj
        else:

            path, execname = os.path.split(sys.argv[0])
            if len(execname) == 0:
                execname="VOMSTools"


            self.logger = logging.getLogger(execname)
            self.logformatter = logging.Formatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s')
            self.logsh.setFormatter(self.logformatter)
            self.logsh = logging.StreamHandler()
            self.logger.addHandler(self.logsh)



            if not self.debug:
                self.logger.setLevel(logging.INFO)
            else:
                self.logger.setLevel(logging.DEBUG)

            if not os.path.exists(LOGDIR):
                self.logger.debug("Log dir %s doesn't exist -- creating!", LOGDIR)
                os.mkdir(LOGDIR)
            self.logpath = os.path.join(LOGDIR,DEFLOGFILE)
            self.logfh = logging.FileHandler(self.logpath)


            self.logfh.setFormatter(self.logformatter)
            self.logger.addHandler(self.logfh)


        self.logger.debug("Starting FERRY SSL business")



#    from Robert Illingworth -- prior to v3.6:
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#    and post 3.6 (untested):
#    self.context=ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.context.load_verify_locations(capath=self.capath)
        self.context.load_cert_chain(HOSTCERT,HOSTKEY)




# Really only one call -- returning a list of DN's that are members of the CMS VO.

    def getDNs(self):


        queryUrl="https://voms2.cern.ch:8443/voms/cms/services/VOMSCompatibility?method=getGridmapUsers"

        self.logger.debug("FERRY Request: %s" % queryUrl)
        try:
            reply = urllib2.urlopen(queryUrl, context=self.context).read().decode('utf8')
        except (urllib2.HTTPError) as err:
            self.logger.critical("Failed to open: %s" % queryUrl)
            self.logger.critical("Error code %i" % err)
            sys.exit(1)
        except (ConnectionRefusedError) as err:
            self.logger.critical("Failed to open: %s" % queryUrl)
            self.logger.critical("Error code %i" % err)
            sys.exit(1)

        replydict=ET.fromstring(reply)

        dnList=[]
        for item in replydict.getiterator():
           if item.tag == 'getGridmapUsersReturn':
              if item.text is not None:
                  dnList.append(item.text)


        self.logger.debug("Parsed xml:")
        self.logger.debug(dnList)

        return (dnList)




if __name__ == '__main__':

    thingy = VOMSTools(cert="/tmp/x509up_u0", capath="/etc/grid-security/certificates")

    myreply=thingy.getDNs(debug=True)


