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
import pwd
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


    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="debug output")

    parser.add_option ("-g", "--group", action="store", dest="group",
                       default=None, help="group")

    (options,args) = parser.parse_args()


    """
    And here we go...
    """

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
        execname="updateEOSgroup"


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


    uidList = []
    newuserList = []

    for user in replyJson:

        logger.debug(user)
        # this is the actual action part -- uidList gets used at bottom in the actual EOS call
        # only do this for CMS members -- meaning expired UID's will get dropped as well
        inCMS=False
        inCMS=Ferry.isInCMS(username=user["username"], debug=options.debug)
        # also don't want to lose the group user from acl list
        if (inCMS | (options.group == user["username"])):
            uidstring="u:"+str(user["uid"])
            uidList.append(uidstring)
            newuserList.append(user["username"])

    logger.debug("uid list: %s", uidList)

    # we by default give ro access to the us_cms group (gid:5063)

    gidList=["g:5063"]

    # now we go to EOS

    eos = EOSTools(mgmnode=EOSMGMHOST, logobj=logger, debug=options.debug)


    grouppath="/eos/uscms/store/user/"+str(options.group)

    rawOutput=""

    rawOutput=eos.fetchacls(path=grouppath)

    logger.debug(rawOutput)

    jsonOutput=json.loads(str(rawOutput))

    acllist=jsonOutput["attr"]["ls"][0]["sys"]["acl"]

    logger.info("Old acl list %s", acllist)

    logger.debug(jsonOutput)

    olduidlist=acllist

# idea here is going to be to pull in the old list, parse & sort to compare with FERRY

    initialuserlist=[]
    # lets pull out the uid's in here
    aclarray=acllist.split(',')
    for thing in aclarray:
        if "u:" in thing:
            uidonly=int(re.sub("\D", "", thing))
            reversename = uidonly
            try:
                reversename = pwd.getpwuid(uidonly).pw_name
            except KeyError:
                logger.warning("UID %s from acl list no longer exists!" % reversename)

            initialuserlist.append(str(reversename))


    logger.info("Old user list in group (from EOS) %s" % options.group)
    droppedusers=[]
    for user in sorted(initialuserlist):
        logger.info(user)
        if user not in newuserList:
            droppedusers.append(user)
            logger.info("%s not in new list, will be dropped" % user)


    addedusers=[]
    logger.info("New user list in group (from FERRY) %s" % options.group)
    for user in sorted(newuserList):
        logger.info(user)
        if user not in initialuserlist:
            inCMS=False
            inCMS=Ferry.isInCMS(username=user, debug=options.debug)
            if (inCMS | (user == options.group)):  # not losing group user
                addedusers.append(user)
                logger.info("%s not in old ACL list, will be added" % user)
            else:
                logger.info("%s not in CMS, will not be added" % user)
                
                
 
    j=eos.setacls(rolist=gidList, rwlist=uidList, path=grouppath)






if __name__ == '__main__':



    main(sys.argv[1:])