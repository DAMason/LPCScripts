 #!/usr/bin/env python3

from __future__ import print_function
import os
import sys
import json
import ssl
import time
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


    parser.add_option("-o", "--output", action="store", type="string",
                      default="grid-mapfile", dest="outputfile",
                      help="output file")


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


    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="CERNUIDList"



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
    logpath = os.path.join(LOGDIR,"GridMap.log")
    logfh = logging.FileHandler(logpath)

    logfh.setFormatter(filelogformatter)
    logger.addHandler(logfh)

    logger.debug("Parsing Options")



    logger.debug("server: %s", options.hosturl)
    logger.debug("capath: %s", options.capath)
    logger.debug("cert: %s", options.cert)
    logger.debug("output: %s", options.outputfile)
    logger.debug("debug: %s", options.debug)

# Get the FERRY bits

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath,
                     logobj=logger)

    logging.debug("Getting FERRY LPC IDs from passwd file")

    replyJson = {}

    replyJson = Ferry.getPasswordInfo(debug=options.debug)

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




    cernuidlist={}

    for user in replyJson["cms"]["resources"]["lpcinteractive"]:
        # to start off we assume uid's are the same, then will override with any
        # CERN ID's we pull down later
        cernuidlist[user["username"]] = user["username"]



    logging.debug("Getting FERRY CERN IDs")

#  we should probably bail if this fails too -- one could argue we write a file with
#  at least the FNAL usernames, but presumably this happened successfully in the past
#  so better to just not update with something incomplete

    replyCERNJson = {}

    replyCERNJson = Ferry.getCERNUserNames(debug=options.debug)


    if len(replyCERNJson) == 0:
        logger.critical("Empty reply from FERRY, aborting!")
        sys.exit(3)


    if "ferry_error" in replyCERNJson:
        # means something is wrong, so we don't want to mess with the existing gridmap
        # without some human eyes somewhere.
        logger.critical("FERRY came back with an error, aborting!")
        logger.critical("Returned json:")
        logger.critical(replyCERNJson)
        sys.exit(2)

    accountAttributes={}

    for k,attrib in replyCERNJson.items():
        logging.debug("%s" % attrib)
        for a in attrib:
           if a['attribute'] == 'cern_username':
               accountAttributes[k] = a['value']
               loggind.debug ("FNAL ID: %s, CERN ID: %s" % (k,accountAttributes[k]))


#  now should have the list of LPC user ID's, mappings of those with CERN
#  ID's as well, so now go through and substitute.

    for fnal,cern in accountAttributes.items():
       if fnal in cernuidlist:
          cernuidlist[fnal]=cern
       else:
          logging.error("%s was not in passwd file! CERN ID: %s",
                         fnal, cern)

#  now we actually have a map of FNAL to CERN uid's to the extent people have
#  given us the CERN UID's  Going to make two files -- one is a map file (probably
#  useful for EOS) and then the list of CERN uid's.for CRAB or whatever.

#  the first guy going to just take options.outputfile and append .map to the end

# paranoid backup into the log dir with timestamp

    if os.path.exists(options.outputfile):
        oldfilesize = os.path.getsize(options.outputfile)
        backupfile = options.outputfile + str(time.time())
        backuppath = os.path.join(LOGDIR,backupfile)
        logging.debug("%s exists, making a backup to %s before writing new uid list",
                      options.outputfile, backuppath)
        shutil.move(options.outputfile,backuppath)

    f = open(options.outputfile, 'w')


#  and for the .map version

    outputmapfilename = options.outputfile + ".map"

    if os.path.exists(outputmapfilename):
        oldmapfilesize = os.path.getsize(outputmapfilename)
        backupfile = outputmapfilename + str(time.time())
        backuppath = os.path.join(LOGDIR,backupfile)
        logging.debug("%s exists, making a backup to %s before writing new uid list",
                      outputmapfilename, backuppath)
        shutil.move(outputmapfilename,backuppath)

    m = open(outputmapfilename, "w")

#   f is the list and m is the map file -- now we just spin over the thing and write.

    for fnal,cern in cernuidlist.items():
          print ("%s %s" % (fnal, cern), file=m)
          print (cern,file=f)

    f.close()

        newfilesize = os.path.getsize(options.outputfile)

    sizediff = newfilesize - oldfilesize
    logging.debug("UID list size change by %i (%2.2f) bytes" % (sizediff,
                  sizediff/oldfilesize*100.0))

    if newfilesize < oldfilesize:
        logging.info("UID list size SHRANK by %i (%2.2f) bytes" % (abs(sizediff),
                     abs(sizediff)/oldfilesize*100.0))

    m.close()

    # sorta moot that this changed the same way...


if __name__ == '__main__':




    main(sys.argv[1:])