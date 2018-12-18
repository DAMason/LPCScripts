 #!/usr/bin/env python3

from __future__ import print_function
import os
import time
import sys
import json
import ssl
from optparse import OptionParser
from LPCScriptsConfig import *
from FERRYTools import *


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

    adayago = time.time()-(60.0*60.0*24.0)
    aweekago = adayago * 7


    parser.add_option("-t", "--timesince", action="store_true", dest="timesince",
                      default=aweekago,
                      help="timestamp of earliest quota")


    (options,args) = parser.parse_args()


    """
    And here we go...
    """

    if options.debug:
        print("server: ", options.hosturl)
        print("capath: ", options.capath)
        print("cert: ", options.cert)
        print("debug: ", options.debug)
        print("timesince: ", options.timesince)




    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath)

    replyJson = Ferry.getRecentQuotas(timestamp=options.timesince, debug=options.debug)

    if not "ferry_error" in replyJson:

        for uid,user in replyJson.items():
            for resource in user:
                 if resource["unit"] == "B":
                     quotaTB = resource["value"]/1000./1000./1000./1000.
                     print (resource["path"] + ": " + quotaTB)
                 else:
                     print (uid + " " resource["path"] + ": " + resource["value"] + resource["unit"])


if __name__ == '__main__':

#  """
#  Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes
#  pre python2.7, so we just go for python3 off the bat.
#  """
#  if (sys.version_info < (3, 0)):
#      print ("run as: python3 detailsCMSUser.py ...")
#      sys.exit()


    main(sys.argv[1:])