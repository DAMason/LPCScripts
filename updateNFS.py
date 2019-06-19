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

    parser.add_option("-u", "--username", action="store", type="string",
                      default=None, dest="username",
                      help="username to force update (other info must be in FERRY)")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False,
                      help="debug output")

    parser.add_option("-n", "--nothing", action="store_true", dest="donothing",
                      default=False,
                      help="check only -- don't perform any action")

    adayago = time.time()-(60.0*60.0*24.0)
          # so that we don't go before the BIG RESET of Apr 8 2019
    aweekago = max(1554730693, time.time()-(60.0*60.0*24.0*7.0))




    parser.add_option("-t", "--timesince", action="store", type="int",
                      dest="timesince",default=aweekago,
                      help="timestamp of earliest quota")


    (options,args) = parser.parse_args()

    """
    And here we go...
    """

    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="updateNFS.py"

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

    logger.info ("NFS update checking beginning...")

    logger.debug("Parsing Options")


    if options.debug:
        logger.debug("server: %s", options.hosturl)
        logger.debug("capath: %s", options.capath)
        logger.debug("cert: %s", options.cert)
        logger.debug("username: %s", options.username)
        logger.debug("donothing: %s", options.donothing)
        logger.debug("debug: %s", options.debug)
        logger.debug("timesince: %s", options.timesince)


    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist...")
        options.cert=None

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath,
                     logobj=logger)

    replyJson = Ferry.getRecentQuotas(timestamp=options.timesince, debug=options.debug)

    logger.debug(replyJson)

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


#    All the preliminaries settled -- made the initial query, now start looping

    logger.info("New quota entries:")

    for uid,user in replyJson['user_quotas'].items():

        logger.debug(user)

        for rid,resource in user.items():

            logger.debug(resource)


            if rid == "NOBACKUP2" || rid == "NOBACKUP3":

                if resource["unit"] == "B":
                    quotaTB = int(resource["value"])/1000./1000./1000./1000.
                    logger.info(uid + " " + resource["path"] + ": " + str(quotaTB) + " TB")
                else:
                    logger.info(uid + " " + resource["path"] + ": " + resource["value"] +
                            resource["unit"])

#            FERRY is giving users quotas on both data2 and data3, but we're currently
#            only adding them to data3.  Need to correct this.

                if os.path.exists(resource["path"]):

                     logger.info(resource["path"] + " exists.")



        logger.info("")


# feeds subprocess and logs results

def scriptexec(command = [], debug=False, logobj=None):

    if logobj is not None and isinstance(logobj,logging.getLoggerClass()):
        logger=logobj
    else:
        print ("scriptexec called without logobj -- skipping doing:")
        print ("%s" % command)
        return 1

#   sticking this in here for debugging
#    command = ["echo"] + command

    logger.debug("Command Array: %s" % command)

    commandstring = ""

    for a in command:
        commandstring = commandstring + a + " "

    logger.info ("Executing: %s" % commandstring)

    output = ""
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        logger.info("Output: %s" % str(output))
    except subprocess.CalledProcessError as e:
        logger.info("Exec Error: %s" % e.output)
        return 2
    except Exception as e:
        logger.info("Other error: %s" % e)
        return 3


    return 0


def fetchquota(path="", logobj=None):

    quotaDict={}

    command = ["quota", "-wp", "-f", path]



    return quotaDict



if __name__ == '__main__':


    main(sys.argv[1:])




