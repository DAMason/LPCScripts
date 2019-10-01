#!/usr/bin/env python3
"""
Bits and pieces needed to make an SSL connection to a https web address.
Assuming python3 here.
"""

import os
import sys
import pwd
import time
import logging

try:
    import urllib.request as urllib2
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2

import ssl
import json
from LPCScriptsConfig import *

from optparse import OptionParser



class FERRYTools(urllib2.HTTPSHandler):



#Set up logging and the SSL bits to talk to FERRY



    def __init__(self, hosturl=FERRYHOSTURL, cert=None,
                 capath=None, logobj=None, debug=False):

        urllib2.HTTPSHandler.__init__(self)
        self.cert = cert
        self.capath = capath
        self.hosturl = hosturl
        self.debug = debug

        if logobj is not None and isinstance(logobj,logging.getLoggerClass()):
            self.logger=logobj
        else:
            path, execname = os.path.split(sys.argv[0])
            if len(execname) == 0:
                execname="FERRYTools"
            self.logger = logging.getLogger(execname)
            self.logformatter =logging.Formatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s')
            self.logsh = logging.StreamHandler()
            self.logsh.setFormatter(self.logformatter)
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


        self.logger.debug("Starting SSL business")









# if we have a cert (either passed from arguments or found to exist in the standard place)
# we'll go and try to establish a proper SSL context -- otherwise we punt and go
# the unverified route -- this looks to be the way to go if operating from a whitelisted
# host.  self.cert assumed to be None if we didn't get one.

        if self.cert is not None:
            self.logger.debug("self.cert: %s " % self.cert)

#        from Robert Illingworth -- prior to v3.6:
            self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#        and post 3.6 (untested):
#        self.context=ssl.SSLContext(ssl.PROTOCOL_TLS)
            self.context.load_verify_locations(capath=self.capath)
            self.context.load_cert_chain(self.cert)

        else:
#           not really nice, but seems to be what we need to do here.
            self.context = ssl._create_unverified_context()



# Generic method to interact with FERRY and try to log what happens


    def genericFerryQuery(self, query, debug=False):
        replyJson = {}
        returnJson = {}
        queryUrl = self.hosturl+query

        self.logger.debug("Request: %s" % queryUrl)
        try:
            reply = urllib2.urlopen(queryUrl, context=self.context).read().decode('utf8')
        except (HTTPError) as err:
            self.logger.critical("Failed to open: %s" % queryUrl)
            self.logger.critical("Error code %s" % err)
            sys.exit(1)
        except (ConnectionRefusedError) as err:
            self.logger.critical("Failed to open: %s" % queryUrl)
            self.logger.critical("Error code %i" % err)
            sys.exit(1)
        except (URLError) as err:
            self.logger.critical("Failed to open: %s" % queryUrl)
            self.logger.critical("Error code %s" % err)
            sys.exit(1)


        self.logger.debug("Returns:")
        self.logger.debug(reply)
        replyJson = json.loads(str(reply))
        self.logger.debug("Json:")
        self.logger.debug(replyJson)

#       in FERRY2 now is supposed to always have a ferry_status, ferry_error,
#       and then ferry_output

        if (type(replyJson) is not dict):
            self.logger.error("Failure trying to deal with %s" % queryUrl)
            self.logger.error("reply isn't expected dict")
        else:
#           SUCCESS
            if (replyJson['ferry_status'] == 'success'):
                returnJson = replyJson['ferry_output']
                self.logger.debug("Returning: %s" % returnJson)
#           ERROR
            else:
                self.logger.error("FERRY returned an error:")
                self.logger.error("Ferry status: %s" % replyJson['ferry_status'])
                self.logger.error("FERRY ERROR: %s" % replyJson['ferry_error'])

        # don't actually abort on FERRY errors -- depends on who's using this
        #  sys.exit(1)
        return returnJson


# individual API calls, essentially converting from a python method to the appropriate
# REST call.


    def getUserInfo(self, username, debug=False):

        replyJson = {}
        query = "/getUserInfo?username=" + username
        replyJson = self.genericFerryQuery(query, debug)


        return replyJson

    def getUserShellandHomedir(self, username, debug=False):

        replyJson = {}
        query = "/getUserShellAndHomeDir?username=" + username + "&resourcename=" + \
                 DEFAULTSTORAGERESOURCE
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson

    def getUserQuotas(self, username, debug=False):

        replyJson = {}
        returnedthing = {}
        query = "/getStorageQuotas?username="+username
        replyJson = self.genericFerryQuery(query, debug)

        if (username in replyJson['users']):
            returnedthing=replyJson['users'][username]
        else:
              self.logger.error("something wrong with returned quota list")
              self.logger.error(replyJson)

        return returnedthing

    def getLPCEOSQuota(self, username, debug=False):
        replyJson = self.getUserQuotas(username, debug)

        return replyJson

    def getUserDNs(self, username, debug=False):

        replyJson = {}
        query = "/getUserCertificateDNs?username="+username
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getUserGroups(self, username, debug=False):

        replyJson = {}
        query = "/getUserGroups?username="+username
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson

    def getPasswordInfo(self, debug=False):

        replyJson = {}
        query = "/getPasswdFile?resourcename=lpcinteractive"
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getGridMap(self, debug=False):

        replyJson = {}
        query = "/getGridMapFile?unitname=cms"
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getGroupMembers(self, groupname="", debug=False):

        replyJson={}

        if len(groupname)> 0:
           query = "/getGroupMembers?groupname=" + groupname
           replyJson = self.genericFerryQuery(query, debug)
        else:
           self.logger.error( "getGroupMembers no group given!")

        return replyJson


    def getCERNUserNames(self, username="", debug=False):

        replyJson = {}

        query = "/getUserExternalAffiliationAttributes"

        if len(username) > 0:
           query = "/getUserExternalAffiliationAttributes?username=" + username

        replyJson = self.genericFerryQuery(query, debug)

        return replyJson



    def getRecentGroups(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getGroupFile?unitname=cms&resourcename=lpcinteractive&lastupdated="
           query = query + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getRecentQuotas(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getStorageQuotas?lastupdated=" + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getRecentUsers(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getAllUsers?lastupdated=" + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getRecentAffiliations(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getUserExternalAffiliationAttributes?lastupdated="
           query = query + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson



    def getMemberships(self, username="", debug=False):

        replyJson = {}

        if len(username) > 0:
           query = "/getMemberAffiliations?username=" + username
           replyJson = self.genericFerryQuery(query, debug)['ferry_output']
           self.logger.debug("getMemberships returning: %s" % replyJson)

        return replyJson


    def isInCMS(self, username="", debug=False):

        isinCMS = False
        replyJson = []
        if len(username) > 0:
            replyJson=self.getMemberships(username, debug)
            self.logger.debug(replyJson)
            if replyJson is not None:
                for affil in replyJson:
                    self.logger.debug(affil)
                    if 'unitname' in affil:
                        self.logger.debug("username: %s, unit: %s",
                                           username,affil['unitname'])
                        if affil['unitname'] == "cms":
                            isinCMS = True

        return isinCMS



# if we're here we're debugging.  FERRY and API tests will commence




if __name__ == '__main__':


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
                      help="username to force create (other info must be in FERRY)")


    adayago = time.time()-(60.0*60.0*24.0)
          # so that we don't go before the BIG RESET of Apr 8 2019
    aweekago = max(1554730693, time.time()-(60.0*60.0*24.0*7.0))


    parser.add_option("-t", "--timesince", action="store", type="int",
                      dest="timesince",default=aweekago,
                      help="timestamp of earliest quota")


    (options,args) = parser.parse_args()

    path, execname = os.path.split(sys.argv[0])
    if len(execname) == 0:
        execname="FERRYTools-TESTING"



# setting up logging -- end up passing this to *Tools so everybody logs to the same place

    logger = logging.getLogger(execname)

    logformatter = logging.Formatter('%(levelname)s %(message)s')
    filelogformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


#   testing -- always debug

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

    logger.info ("Various FERRY tests beginning...")

    logger.debug("Parsing Options")

    logger.debug("server: %s", options.hosturl)
    logger.debug("capath: %s", options.capath)
    logger.debug("cert: %s", options.cert)
    logger.debug("username: %s", options.username)
    logger.debug("timesince: %s", options.timesince)


    """
    And here we go...
    """

#   Catching if there isn't a cert -- then passing None

    if not os.path.exists(options.cert):
        logger.info("cert: %s not found -- proceeding to assume host is in whitelist..."%
                    options.cert)

        options.cert=None


    thingy = FERRYTools(hosturl=options.hosturl, cert=options.cert,
                        capath=options.capath, debug=True, logobj=logger)



