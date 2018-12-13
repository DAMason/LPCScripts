 #!/usr/bin/env python3
"""
Use a combination of FERRY and the CMS VOMS server to produce a gridmap file for CRAB
users on the T1
"""


from __future__ import print_function
import os
import time
import sys
import shutil
import json
import ssl
import re
import datetime
from optparse import OptionParser
from LPCScriptsConfig import *
from FERRYTools import *
from EOSTools import *




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
                      help="FERRY Server host URL")

    parser.add_option("-p", "--capath", action="store", type="string",
                      default=CAPATH, dest="capath",
                      help="CA Path")

    defaultcertloc = "/tmp/x509up_u"+str(os.getuid())

    parser.add_option("-c", "--cert", action="store", type="string",
                      default=defaultcertloc, dest="cert",
                      help="full path to cert")

    parser.add_option("-u", "--username", action="store", type="string",
                      default=None, dest="username",
                      help="username to show details of")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="debug output")

    parser.add_option ("-g", "--group", action="store", dest="group",
                       default=None, help="group")

    (options,args) = parser.parse_args()


    """
    And here we go...
    """

    if not options.username:
        print("providing the username is rather required")
        parser.print_help()
        sys.exit(1)

    if not options.group:
        print("providing the username is rather required")
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist..        .")
        options.cert=None


    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="addusertoEOSgroup"


# setting up logging -- end up passing this to *Tools so everybody logs to the same place

    logger = logging.getLogger(execname)

    logformatter = logging.Formatter('%(levelname)s %(message)s')
    filelogformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


    if not options.debug:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    logsh = logging.StreamHandler()

    logsh.setFormatter(logformatter)
    logger.addHandler(logsh)


    if not os.path.exists(LOGDIR):
        logger.debug("Log dir %s doesn't exist -- creating!", LOGDIR)
        os.mkdir(LOGDIR)
    logfilename=execname+".log"
    logpath = os.path.join(LOGDIR,logfilename)
    logfh = logging.FileHandler(logpath)

    logfh.setFormatter(filelogformatter)
    logger.addHandler(logfh)

    logger.debug("Parsing Options")



    logger.debug("server: %s", options.hosturl)
    logger.debug("capath: %s", options.capath)
    logger.debug("cert: %s", options.cert)
    logger.debug("group: %s", options.group)
    logger.debug("user: %s", options.username)
    logger.debug("debug: %s", options.debug)


# Get the FERRY bits

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath,
                     logobj=logger)

    groupusers = {}

    replyJson = {}

    replyJson = Ferry.getGroupMembers(groupname=options.group, debug=options.debug)

    logger.debug("Fetching userlist for group: %s", options.group)

    if len(replyJson) == 0:
        logger.critical("Empty reply from FERRY, aborting!")
        sys.exit(3)

    if "ferry_error" in replyJson:
        # means something is wrong, so we don't want to mess with the existing gridmap
        # without some human eyes somewhere.
        logger.critical("FERRY came back with an error, aborting!")
        logger.critical("Returned json:")
        logger.critical(replyJson)
        sys.exit(2)

    uidList=[]

    for user in replyJson:

        logger.debug(user)

        uidstring="u:"+str(user["uid"])
        uidList.append(uidstring)

    logger.debug("uid list: %s", uidList)

    # we by default give ro access to the us_cms group (gid:5063)

    gidList=["g:5063"]

    # now we go to EOS

    eos = EOSTools(mgmnode=EOSMGMHOST, logobj=logger, debug=options.debug)

    grouppath="/eos/uscms/store/user"+str(options.group)

    j=eos.setacls(rolist=gidList, rwlist=uidList, path=grouppath)






if __name__ == '__main__':



    main(sys.argv[1:])