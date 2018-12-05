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

    parser.add_option("-o", "--output", action="store", type="string",
                      default="grid-mapfile", dest="outputfile",
                      help="output file")

    parser.add_option("-i", "--input", action="store", type="string",
                      default=HARDWIREDGRIDMAP, dest="inputfile",
                      help="input file for hardwired gridmaps")

    (options,args) = parser.parse_args()


    """
    And here we go...
    """

    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist..        .")
        options.cert=None


    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="GridMap"


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
    logger.debug("output: %s", options.outputfile)
    logger.debug("input: %s", options.inputfile)
    logger.debug("debug: %s", options.debug)


# Get the FERRY bits

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath,
                     logobj=logger)

    replyJson = Ferry.getGridMap(options.debug)

    fnalmap = {}

# ATM if we can't get a hold of FERRY looks like we map everyone to the default user
#     except the hardwired maps


    logging.debug("Getting FERRY mapped IDs")


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


    for user in replyJson:

#   important for the LPC to strip off the cilogon certs

        if not "cilogon" in user['userdn']:
            fnalmap[user['userdn']] = user['mapped_uname']

            logger.debug("%s  %s" %(user['mapped_uname'], user['userdn']))


    Voms=VOMSTools(cert=options.cert, capath=options.capath, logobj=logger)

    VomsDNList = Voms.getDNs()

    for dn in VomsDNList:

        if dn not in fnalmap:
            fnalmap[dn]=CMSDEFAULTPOOLUSER

#   pulling in the hardwired gridmap file if it exists.  Do this last since we're
#   overriding what is in so far.  Expecting the hw gridmap file to be formatted like
#   an actual gridmap file.

    hwmap = {}
    if os.path.exists(options.inputfile):
        with open(options.inputfile, 'r') as hwinput:
            for line in hwinput:
                hwdn=re.findall(r'\"(.+?)\"',line)
                hwuname=line.split()[-1]
                logger.debug("user: %s, dn: %s" % (hwuname,hwdn))
                fnalmap[hwdn[0]] = hwuname

    else:
        logger.info("No hardwired input file: %s found, proceeding without...",
                    options.inputfile)

# paranoid backup into the log dir with timestamp

    oldfilesize = 1

    if os.path.exists(options.outputfile):
        oldfilesize = os.path.getsize(options.outputfile)
        backupfile = options.outputfile + str(time.time())
        backuppath = os.path.join(LOGDIR,backupfile)
        logger.debug("%s exists, making a backup to %s before writing new gridmap",
                      options.outputfile, backuppath)
        shutil.move(options.outputfile,backuppath)

    f = open(options.outputfile, 'w')

    for dn,user in fnalmap.items():
       print ('"%s" %s'%(dn,user),file=f)


    f.close()

    newfilesize = os.path.getsize(options.outputfile)

    sizediff = newfilesize - oldfilesize
    logger.debug("Gridmap size change by %i (%2.2f) bytes" % (sizediff,
                  sizediff/oldfilesize*100.0))

    if newfilesize < oldfilesize:
        logger.info("Gridmap size SHRANK by %i (%2.2f) bytes" % (abs(sizediff),
                     abs(sizediff)/oldfilesize*100.0))


if __name__ == '__main__':



    main(sys.argv[1:])