#!/usr/bin/env python3
"""
Bits and pieces needed to make an SSL connection to a https web address.
Assuming python3 here.
"""

import os
import sys
import urllib.request as urllib2
import ssl 
import json
from LPCScriptsConfig import *

class FERRYTools(urllib2.HTTPSHandler):
     
    def __init__(self, hosturl=FERRYHOSTURL, cert=None, capath=None):

       self.cert=cert
       self.capath=capath
       self.hosturl=hosturl

#      from Robert Illingworth -- prior to v3.6:       
       self.context=ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#      and post 3.6 (untested):
#      self.context=ssl.SSLContext(ssl.PROTOCOL_TLS)
       self.context.load_verify_locations(capath=self.capath)
       self.context.load_cert_chain(self.cert)

#getUser API call, returns dictionary

    def genericFerryQuery(self,query,debug=False):
       replyJson={}
       queryUrl=self.hosturl+query
       if (debug):
         print ("Request: %s" % queryUrl)
       try:
          reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       except (urllib2.HTTPError) as err:
         print ("Failed to open: %s" % queryUrl)
         print ("Error code %i" % err)
         sys.exit(1)
       except (ConnectionRefusedError) as err:
         print ("Failed to open: %s" % queryUrl)
         print ("Error code %i" % err)
         sys.exit(1)

       
       if (debug): 
         print ("Returns:")
         print (reply)
       replyJson=json.loads(str(reply))
       if (debug):
         print ("Json:")
         print ("replyJson")
       # seems ferry errors are a dict independent of whatever you are expecting
       if (type(replyJson) is dict and "ferry_error" in replyJson.keys()):
         print ("Failure trying to deal with: %s" % queryUrl)
         # dealing with {"ferry_error",None}
         if (replyJson['ferry_error'] is not None):
           print ("Ferry Error:    " + replyJson['ferry_error'])
         else:
           print (replyJson)
         sys.exit(1)
       return replyJson

    def getUserInfo(self,username,debug=False):   
        
       replyJson={}
       query="/getUserInfo?username="+username
       replyJson=self.genericFerryQuery(query,debug)

       
       return replyJson
       
    def getUserShellandHomedir(self,username,debug=False):   
        
       replyJson={}
       query="/getUserShellAndHomeDir?username="+username+"&resourcename="+DEFAULTSTORAGERESOURCE
       replyJson=self.genericFerryQuery(query,debug)

       
       return replyJson
       
    def getUserQuotas(self,username,debug=False):   
        
       replyJson={}
       query="/getUserAllStorageQuotas?username="+username
       replyJson=self.genericFerryQuery(query,debug)

       return replyJson
       
    def getUserDNs(self,username,debug=False):   
        
       replyJson={}
       query="/getUserCertificateDNs?username="+username
       replyJson=self.genericFerryQuery(query,debug)
       
       return replyJson       
       
       
    def getUserGroups(self,username,debug=False):   
        
       replyJson={}
       query="/getUserGroups?username="+username
       replyJson=self.genericFerryQuery(query,debug)

       
       return replyJson          
       
       
if __name__=='__main__':
         
     thingy=FERRYTools(cert="/tmp/x509up_u0", capath="/etc/grid-security/certificates")