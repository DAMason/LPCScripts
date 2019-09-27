#!/usr/bin/env python3

from __future__ import print_function
import os
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
                      help="username to show details of")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="debug output")

    (options,args) = parser.parse_args()


    """
    And here we go...
    In some of the dependent bits, like FERRYTools, have converted prints to logging
    calls -- doesn't make a lot of sense for this though since its primarily a display
    tool -- keeping the print statements and if's on options.debug
    """

    if not options.username:
        print("providing the username is rather required")
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist...")
        options.cert=None

    if options.debug:
        print("server: ", options.hosturl)
        print("capath: ", options.capath)
        print("cert: ", options.cert)
        print("debug: ", options.debug)



    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert,
                     capath=options.capath, debug=options.debug)


    print("\nDisplaying details for user: ", options.username)

    # first getUserInfo

    replyJson = Ferry.getUserInfo(options.username, options.debug)

    print("Full Name:       ", replyJson['fullname'])
    print("UID:             ", replyJson['uid'])
    print("Status:          ", replyJson['status'])
    print("Exp. Date        ", replyJson['expiration_date'])

    replyJson = Ferry.getUserShellandHomedir(options.username, options.debug)
    print("Home dir         ", replyJson['homedir'])
    print("Shell            ", replyJson['shell'])


    replyJson = Ferry.getCERNUserNames(username=options.username,debug=options.debug)

    cernusername=options.username

    try:
        cernusername = replyJson[options.username][0]["value"]
    except:
        print("No CERN Affiliation set in FERRY")

    print("CERN Username: %s" % cernusername)


    print("\nStorage Quotas:")

    replyJson = Ferry.getUserQuotas(options.username, options.debug)
#    for resource in replyJson:
#        print(resource['resourcename'].ljust(10), end=' ')
    if options.debug:
        print ("replyJson[user_quotas][options.username]: %s" %
               replyJson["user_quotas"][options.username])

    for k,resource in replyJson["user_quotas"][options.username].items():
        if options.debug:
            print ("resource %s" % resource)

        print(k.ljust(10), end=' ')
        print(resource['value'].rjust(15), resource['unit'].ljust(5), end=' ')
        print(resource['path'].ljust(30), resource['validuntil'].ljust(20))




    print("\nGroups")

    replyJson = Ferry.getUserGroups(options.username, options.debug)
    for group in replyJson:
        print(str(group['gid']).ljust(6), group['groupname'].rjust(20),
              group['grouptype'].ljust(10))



    print("\n DN\'s")
    replyJson = Ferry.getUserDNs(options.username, options.debug)
    if not "ferry_error" in replyJson:
        for dn in replyJson[0]['certificates']:
            print(dn)



if __name__ == '__main__':

#  """
#  Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes
#  pre python2.7, so we just go for python3 off the bat.
#  """
#  if (sys.version_info < (3, 0)):
#      print ("run as: python3 detailsCMSUser.py ...")
#      sys.exit()


    main(sys.argv[1:])


