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
       
       self.context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)
       self.context.load_verify_locations(capath=self.capath)
       self.context.load_cert_chain(self.cert)

#getUser API call, returns dictionary

    def genericFerryQuery(query):
       replyJson={}
       queryUrl=self.hosturl+query
       reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       replyJson=json.loads(str(reply))
       if ("ferry_error" in replyJson.keys()):
         print ("Ferry Error:" + replyJson['ferry_error'])
         sys.exit(1)
       return replyJson

    def getUserInfo(self,username):   
        
       replyJson={}
       query="/getUserInfo?username="+username
       replyJson=genericFerryQuery(query)
   #    queryUrl=self.hosturl+"/getUserInfo?username="+username
   #    reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
   #    replyJson=json.loads(str(reply))
       
       return replyJson
       
    def getUserShellandHomedir(self,username):   
        
       replyJson={}
       queryUrl=self.hosturl+"/getUserShellAndHomeDir?username="+username+"&resourcename="+DEFAULTSTORAGERESOURCE
       reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       replyJson=json.loads(str(reply))
       
       return replyJson
       
    def getUserQuotas(self,username):   
        
       replyJson={}
       queryUrl=self.hosturl+"/getUserAllStorageQuotas?username="+username
       reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       replyJson=json.loads(str(reply))
       
       return replyJson
       
    def getUserDNs(self,username):   
        
       replyJson={}
       queryUrl=self.hosturl+"/getUserCertificateDNs?username="+username
       reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       replyJson=json.loads(str(reply))
       
       return replyJson       
       
       
    def getUserGroups(self,username):   
        
       replyJson={}
       queryUrl=self.hosturl+"/getUserGroups?username="+username
       reply=urllib2.urlopen(queryUrl,context=self.context).read().decode('utf8')
       replyJson=json.loads(str(reply))
       
       return replyJson          
       
       
if __name__=='__main__':
         
     thingy=FERRYTools(cert="/tmp/x509up_u0", capath="/etc/grid-security/certificates")