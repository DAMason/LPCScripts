#!/usr/bin/env python3
"""
Bits and pieces needed to make an SSL connection to a https web address.
Assuming python3 here.
"""

import os
import sys
import logging

try:
    import urllib.request as urllib2
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2

import ssl
import json
from LPCScriptsConfig import *


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
        # seems ferry errors are a dict independent of whatever you are expecting
        if (type(replyJson) is dict and "ferry_error" in replyJson.keys()):
            self.logger.info("Failure trying to deal with: %s" % queryUrl)
         # dealing with {"ferry_error",None}
            if replyJson['ferry_error'] is not None:
                self.logger.info("Ferry Error:    " + str(replyJson['ferry_error']))
            else:
                print(replyJson)

        # don't actually abort on FERRY errors -- depends on who's using this
        #  sys.exit(1)
        return replyJson


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
        query = "/getStorageQuotas?username="+username
        replyJson = self.genericFerryQuery(query, debug)

        return replyJson

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



    def getRecentQuotas(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getStorageQuotas?last_updated=" + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getRecentUsers(self, timestamp=0, debug=False):

        replyJson = {}

        if timestamp > 0:
           query = "/getAllUsers?last_updated=" + str(int(timestamp))
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def getMemberships(self, username="", debug=False):

        replyJson = {}

        if len(username) > 0:
           query = "/getMemberAffiliations?username=" + username
           replyJson = self.genericFerryQuery(query, debug)

        return replyJson


    def isInCMS(self, username="", debug=False):

        isinCMS = False
        replyJson = []
        if len(username) > 0:
            replyJson=self.getMemberships(username, debug)
            self.logger.debug(replyJson)
            for affil in replyJson:
                self.logger.debug("username: %s, unit: %s", username,affil['unitname'])
                if affil['unitname'] == "cms":
                    isinCMS = True

        return isinCMS







if __name__ == '__main__':

    thingy = FERRYTools(cert="/tmp/x509up_u0", capath="/etc/grid-security/certificates")
