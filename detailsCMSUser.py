#!/usr/bin/env python3

import os
import sys
import json
import urllib.request as urllib2
import ssl
from optparse import OptionParser
from LPCScriptsConfig import *
from FERRYTools import *


"""
Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes 
pre python2.7, so we just go for python3 off the bat.
"""
if not sys.version.startswith('3.'):
  print ("python3 please...")
  sys.exit()
  
                
"""
The meat of the thing
"""
def main(argv):

   #print ("whoopee",argv[0])
   
   
   """
   Options
   """
   usage = "Usage: %prog [options] thing\n"
   parser=OptionParser(usage=usage)
   parser.add_option("-s", "--server", action="store", type="string", 
                     default=FERRYHOSTURL, dest="hosturl", 
                     help="Server host URL")
   
   parser.add_option("-p", "--capath", action="store", type="string",
                     default=CAPATH, dest="capath",
                     help="CA Path")
                     
   defaultcertloc="/tmp/x509up_u"+str(os.getuid())                  
                     
   parser.add_option("-c", "--cert", action="store", type="string",
                     default=defaultcertloc, dest="cert",
                     help="full path to cert")
                     
   parser.add_option("-u", "--username", action="store", type="string",
                     default=None, dest="username",
                     help="username to show details of")
                     
   parser.add_option("-d", "--debug", action="store_true", dest="debug",
                     help="debug output")
   
   (options,args)=parser.parse_args()
   
   
   """
   And here we go...
   """   
   
   if not options.username:
     print ("providing the username is rather required")
     parser.print_help()
     sys.exit(1)
     


   print("server: ",options.hosturl)  
   print("capath: ",options.capath)
   print("cert: ",options.cert)
   
   
   Ferry=FERRYTools(hosturl=options.hosturl,cert=options.cert,capath=options.capath)  

   
   print("\nDisplaying details for user: ",options.username)

   # first getUserInfo   
   
   replyJson=Ferry.getUserInfo(options.username)

   print ("Full Name:       ",replyJson[0]['full_name'])
   print ("UID:             ",replyJson[0]['uid'])
   print ("Status:          ",replyJson[0]['status'])
   print ("Exp. Date        ",replyJson[0]['expiration_date'])

   replyJson=Ferry.getUserShellandHomedir(options.username)
   print ("Home dir         ",replyJson[0]['homedir'])
   print ("Shell            ",replyJson[0]['shell'])

   print ("\nStorage Quotas:")
   
   replyJson=Ferry.getUserQuotas(options.username)
   for resource in replyJson:
     print (resource['resourcename'].ljust(10),end=' ')
     print (resource['value'].rjust(15),resource['unit'].ljust(5),end=' ')
     print (resource['path'].ljust(30),resource['validuntil'].ljust(20))
     
     
     

   print ("\nGroups")

   replyJson=Ferry.getUserGroups(options.username)
   for group in replyJson:
     print (str(group['gid']).ljust(6),group['groupname'].rjust(20),group['grouptype'].ljust(10))
     
     

   print ("\n DN\'s")
   replyJson=Ferry.getUserDNs(options.username)
   for dn in replyJson[0]['certificates']:
     print(dn)

   
   
if __name__=='__main__':
  main(sys.argv[1:])
  




