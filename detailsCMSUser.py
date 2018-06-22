#!/usr/bin/env python3

import os
import sys
import urllib.request as urllib2
import ssl
from optparse import OptionParser
from LPCScriptsConfig import *


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
   
   print("\nDisplaying details for user: ",options.username)

   
   
   testqueryurl=options.hosturl+"/getUserInfo?username="+options.username
   
   context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)
   context.load_verify_locations(capath=options.capath)
   context.load_cert_chain(options.cert)

   f=urllib2.urlopen(testqueryurl,context=context)

   print (f.read())
   
 
 
 
 
   
if __name__=='__main__':
  main(sys.argv[1:])
  




