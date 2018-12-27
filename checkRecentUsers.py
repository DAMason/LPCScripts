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

    parser.add_option("-n", "--nothing", action="store_true", dest="donothing",
                      help="check only -- don't perform any action")

    adayago = time.time()-(60.0*60.0*24.0)
    aweekago = time.time()-(60.0*60.0*24.0*7.0)


    parser.add_option("-t", "--timesince", action="store", type="int",
                      dest="timesince",default=aweekago,
                      help="timestamp of earliest quota")


    (options,args) = parser.parse_args()


    """
    And here we go...
    """



    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="checkRecentUsers.py"


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

    logger.info ("New user checking beginning...")

    logger.debug("Parsing Options")



    if options.debug:
        logger.debug("server: %s", options.hosturl)
        logger.debug("capath: %s", options.capath)
        logger.debug("cert: %s", options.cert)
        logger.debug("donothing: %s", options.donothing)
        logger.debug("debug: %s", options.debug)
        logger.debug("timesince: %s", options.timesince)


    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist...")
        options.cert=None

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath)

    replyJson = Ferry.getRecentUsers(timestamp=options.timesince, debug=options.debug)


    logger.debug(replyJson)

    if not "ferry_error" in replyJson:


        userlist = []

        for user in replyJson:
            if options.debug:
                 logger.debug("anybody: %s", user)
            if Ferry.isInCMS(username=user['username'], debug=options.debug):
                logger.info("New cms user: " + str(user['username']) + "  " +
                            str(user['uid']) + "  " + str(user['full_name']) + "  " +
                            str(user['expiration_date']))

                userlist.append(user['username'])
                useruidlist.append(user['uid'])

#                if not os.path.exists()



if __name__ == '__main__':

#  """
#  Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes
#  pre python2.7, so we just go for python3 off the bat.
#  """
#  if (sys.version_info < (3, 0)):
#      print ("run as: python3 detailsCMSUser.py ...")
#      sys.exit()


    main(sys.argv[1:])