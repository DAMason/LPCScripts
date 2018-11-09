 #!/usr/bin/env python3
"""
Use a combination of FERRY and the CMS VOMS server to produce a gridmap file for CRAB
users on the T1
"""


from __future__ import print_function
import os
import sys
import json
import ssl
from optparse import OptionParser
from LPCScriptsConfig import *
from FERRYTools import *
from VOMSTools import *


"""
The meat of the thing
"""

def main(argv):


    """
    Options
    """
    usage = "Usage: %prog [options] thing\n"
    parser = OptionParser(usage=usage)

    parser.add_option("-s", "--server", action="store", type="string",
                      default=FERRYHOSTURL, dest="hosturl",
                      help="Server host URL")

    parser.add_option("-p", "--capath", action="store", type="string",
                      default=CAPATH, dest="capath",
                      help="CA Path")

    defaultcertloc = "/tmp/x509up_u"+str(os.getuid())

    parser.add_option("-c", "--cert", action="store", type="string",
                      default=defaultcertloc, dest="cert",
                      help="full path to cert")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="debug output")

    (options,args) = parser.parse_args()


    """
    And here we go...
    """

    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist..        .")
        options.cert=None


    if options.debug:
        print("server: ", options.hosturl)
        print("capath: ", options.capath)
        print("cert: ", options.cert)
        print("debug: ", options.debug)


    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath)

    replyJson = Ferry.getGridMap(options.debug)

    if not "ferry_error" in replyJson:

        if options.debug:
            for user in replyJson:
                print ("%s  %s" %(user['mapped_uname'], user['userdn']))



    Voms=VOMSTools(cert=options.cert, capath=options.capath)

    VomsDNList=Voms.getDNs(debug=options.debug)


if __name__ == '__main__':

#  """
#  Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes
#  pre python2.7, so we just go for python3 off the bat.
#  """
#  if (sys.version_info < (3, 0)):
#      print ("run as: python3 detailsCMSUser.py ...")
#      sys.exit()


    main(sys.argv[1:])