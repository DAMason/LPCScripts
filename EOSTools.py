"""
Bits and pieces of things useful to interact with EOS on the LPC
Assuming python3 here

Modifications of quotas & such need to be done by root on the mgm.

"""


import os
import sys
import logging

from LPCScriptsConfig import *

class EOSTools:

    def __init__(self, mgmnode=EOSMGMHOST, logobj=None, debug=False):

        self.mgmnode = mgmnode
        self.debug = debug

# check where we are -- if we're sitting on the mgmnode, then we just execute direct,
# if we aren't we need to assume we can ssh as root to the mgm node.  We can check that
# when we start

        self.hostname = os.uname()[1]
        self.local = False
        if self.hostname==mgmnode:
            self.local = True


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



# exec wrapper that either locally or via ssh runs the passed EOS command on the mgm

    def mgmexec(self,debug=False):


        return 0


    def fetchuserquotas(self, user=None):


        return 1

#   Fetches acls for a path to check against.

    def getacls(self, path=None):



#  Sets the acls for a group dir -- expecting lists of uid's presumably retrieved from
#  FERRY, and a path to apply the resulting ACL's to.

    def setacls(self, rolist=[], rwlist=[], path=None):

#       rx!d!u should mean read (r), browse (x), NOT delete (!d)), NOT overwrite (!u)
#       historically this was applied to the us_cms group
        ROACLSTRING = "rx!d!u"
#       rwx+d+u should mean rwx = read,write,browse +d = delete, +u = overwrite
#       historically this has then been applied to user members of an LPC physics group
        RWACLSTRING = "rwx+d+u"

#       so we're assuming the rolist and rwlist will contain entries like g:gid and
#       u:uid  as in with the "g:" and "u:" to differentiate groups and users.

        if not path:
            self.logger.error ("No path given, not setting ACLs")
            return -1

        if len(rolist)==0 and len(rwlist)==0:
            self.logger.error ("No acls given, not doing anything")
            return -1

#       construct the acl list now:

        aclstring=''

        self.logger.debug ("rolist given %s", rolist)
        for ro in rolist:
            aclstring = aclstring + ro + ":" + ROACLSTRING

        self.logger.debug ("rwlist given %s", rwlist)
        for rw in rwlist:
            aclstring = aclstring + rw + ":" + RWACLSTRING

        self.logger.debug("Full ACL string: %s", aclstring)

        aclsetcommand = "{eoscommand} 'attr -r set sys.acl={aclstring} {path}'".format(
                        EOSSHELL, aclstring, path)

        self.logger.debug("ACL Command: %s", aclsetcommand)

        return 0



if __name__ == '__main__':

    thingy = EOSTools(mgmnode="cmseosmgm01.fnal.gov")