#!/usr/bin/env python3

from __future__ import print_function
import os
import pwd
import time
import sys
import json
import ssl
import subprocess
from shlex import quote
from optparse import OptionParser
from LPCScriptsConfig import *
from FERRYTools import *
from EOSTools import *
from EmailTools import *



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
                      help="username to force create (other info must be in FERRY)")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False,
                      help="debug output")

    parser.add_option("-n", "--nothing", action="store_true", dest="donothing",
                      default=False,
                      help="check only -- don't perform any action")

    adayago = time.time()-(60.0*60.0*24.0)
          # so that we don't go before the BIG RESET of Apr 8 2019
    aweekago = max(1554730693, time.time()-(60.0*60.0*24.0*7.0))




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
        logger.debug("username: %s", options.username)
        logger.debug("donothing: %s", options.donothing)
        logger.debug("debug: %s", options.debug)
        logger.debug("timesince: %s", options.timesince)


    if not os.path.exists(options.cert):
        print("cert: ", options.cert,
              " not found -- proceeding to assume host is in whitelist...")
        options.cert=None

    Ferry=FERRYTools(hosturl=options.hosturl, cert=options.cert, capath=options.capath,
                     logobj=logger)

    # hacked this in to force account check/creation for a known user that the time based
    # query doesn't pull up.  getUserInfo returns an array of users so next line does
    # a minor tweak to make same format as what comes back from getRecentUsers -- then
    # the rest behaves the same:

    replyJson=[];
    
    if options.username is not None:
    
#       normally this will be a list, so tacking the one user onto it
        replyJson.append(Ferry.getUserInfo(username=options.username, 
                                           debug=options.debug))
        replyJson[0]=options.username

    else:

        replyJson = Ferry.getRecentUsers(timestamp=options.timesince, debug=options.debug)



    logger.debug(replyJson)

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


    userlist = []
    useruidlist = []
    userfullnamemap = {}

    for user in replyJson:
        logger.debug("anybody: %s", user)
        if Ferry.isInCMS(username=user['username'], debug=options.debug):
            logger.info("New cms user: " + str(user['username']) + "  " +
                        str(user['uid']) + "  " + str(user['gecos']))  # + "  " 
#                        str(user['expirationdate']))  # not in passwd file 
            userfullnamemap[user['username']]=user['gecos']

            try:
                pwd.getpwnam(user['username'])
                userlist.append(user['username'])
                useruidlist.append(user['uid'])
            except KeyError:
                logger.info("User %s does not exist on the system yet, skipping for now" %
                            user['username'])





    logger.info("Walking through new users:")

#   Here we go through the latest users and start checking that the relevant physical
#   bits and pieces are where they need to be.

#   get ready to do stuff with EOS if necessary

    eos = EOSTools(mgmnode=EOSMGMHOST, logobj=logger, debug=options.debug)


#   also set up mail bits

    email = EmailTools(logobj=logger, debug=options.debug)


    for user in userlist:

        replyJson = {}

        replyJson = Ferry.getUserShellandHomedir(user, options.debug)
        homedir = replyJson['homedir']

        if os.path.exists(homedir):

            logger.info("Homedir: %s exists", homedir)

        else:
             
            logger.info("Homedir: %s DOES NOT EXIST", homedir)
            
            sanitizedusername=quote(user)

            logger.debug("Sanitizing username %s into: %s" % (user,sanitizedusername))
                        
            j = scriptexec(command=["ssh","cmseosmgm01.fnal.gov","id", sanitizedusername], debug=options.debug,
                           logobj=logger)
                           
            j = scriptexec(command=["ssh","cmsnfs2.fnal.gov", "id", sanitizedusername], debug=options.debug,
                           logobj=logger)
                           
                           

            if not options.donothing:

#                sanitizedusername=quote(user)

#                logger.debug("Sanitizing username %s into: %s" % (user,sanitizedusername))

#               We're not going to rely on discovering these things from FERRY just yet
#               First make the /uscms/homes guy, then make the link.

#                Historically:

#                mkdir /uscms/homes/u/username
#                ln -s /uscms/homes/u/username /uscms/home/username
#                mkdir -p /uscms/homes/u/username/work
#                mkdir -p /uscms/homes/u/username/private
#                mkdir -p /uscms/homes/u/username/.globus
#
#                mkdir -p /uscms/data/d3/username
#                ln -s /uscms_data/d3/user /uscms_data/d1/username
#                ln -s /uscms_data/d1/user /uscms/homes/u/username/nobackup

#                chown -R user.us_cms /uscms/homes/u/username
#                chown -R user.us_cms /uscms_data/d3/username
#                chown -R user.us_cms /uscms_data/d1/username

#                chmod 700 /uscms/homes/u/username/.globus
#                chmod 755 /uscms/homes/u/username
#                chmod 755 /uscms/homes/u/username/work
#                chmod 700 /uscms/homes/u/username/private
#                chmod 755 /uscms_data/d3/username




#                EOS things:


#                /usr/bin/eos -b mkdir /eos/uscms/store/user/username
#                /usr/bin/eos -b chown username:us_cms /eos/uscms/store/user/username
#                ls -ald /eos/uscms/store/user/username
#                /usr/bin/eos -b quota set -u username -v 4TB -i 500000 /eos/uscms/store/user/



                usernamefirstchar = sanitizedusername[0]
                realhomedir = "/uscms/homes/" + usernamefirstchar + "/"
                realhomedir = realhomedir + sanitizedusername
                j = scriptexec(command=["mkdir", realhomedir], debug=options.debug,
                           logobj=logger)

                oldhomedir = "/uscms/home/" + sanitizedusername
                j = scriptexec(command=["ln", "-s", realhomedir, oldhomedir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["mkdir", "-p", realhomedir+"/work"],
                           debug=options.debug, logobj=logger)

                j = scriptexec(command=["mkdir", "-p", realhomedir+"/private"],
                           debug=options.debug, logobj=logger)

                j = scriptexec(command=["mkdir", "-p", realhomedir+"/.globus"],
                               debug=options.debug, logobj=logger)

#               NFS stuff

                nfsdir = "/uscms_data/d3/" + sanitizedusername

                linknfsdir = "/uscms_data/d1/" + sanitizedusername

                j = scriptexec(command=["mkdir", "-p", nfsdir],
                           debug=options.debug, logobj=logger)

#               this is hardwired at the moment
                quotastring = "limit -u bsoft=100g bhard=120g " + sanitizedusername

                j = scriptexec (command=["xfs_quota", "-x", "-c", '"'+quotastring+'"',
                                         "/uscms_data/d3"],
                                debug=options.debug, logobj=logger)


                j = scriptexec(command=["ln", "-s", nfsdir, linknfsdir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["ln", "-s", linknfsdir, realhomedir+"/nobackup"],
                               debug=options.debug, logobj=logger)

#               setting permissions

                j = scriptexec(command=["chown", "-R", sanitizedusername+".us_cms",
                                        realhomedir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chown", "-R", sanitizedusername+".us_cms",
                                        nfsdir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chown", "-R", sanitizedusername+".us_cms",
                                        linknfsdir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "755", realhomedir],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "700", realhomedir+"/.globus"],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "755", realhomedir+"/work"],
                              debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "700", realhomedir+"/private"],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "755", nfsdir],
                               debug=options.debug, logobj=logger)

#      skeleton .bash_profile also committed along with this code -- copy to homedir

                j = scriptexec(command=["cp", "./proto_bash_profile",
                               realhomedir+"/.bash_profile"],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chown", sanitizedusername+".us_cms",
                               realhomedir+"/.bash_profile"],
                               debug=options.debug, logobj=logger)

                j = scriptexec(command=["chmod", "644",
                               realhomedir+"/.bash_profile"],
                               debug=options.debug, logobj=logger)


#      then EOS -- relies being able to log into the MGM

                rawoutput=""

                eosdir = "/eos/uscms/store/user/" + sanitizedusername
                eosexecstring = "mkdir " + eosdir
                logger.debug(eosexecstring)
                rawoutput = eos.mgmexec(execstring=eosexecstring, debug=options.debug)
                logger.info ("EOS returns: %s" % rawoutput)

                eosexecstring = "chown " + sanitizedusername + ":us_cms " + eosdir
                logger.debug(eosexecstring)
                rawoutput = eos.mgmexec(execstring=eosexecstring, debug=options.debug)
                logger.info ("EOS returns: %s" % rawoutput)

                eosexecstring = "quota set -u " + sanitizedusername + " -v 4TB -i 500000 "
                eosexecstring = eosexecstring + "/eos/uscms/store/user"
                logger.debug(eosexecstring)
                rawoutput = eos.mgmexec(execstring=eosexecstring, debug=options.debug)
                logger.info ("EOS returns: %s" % rawoutput)


#      done with the physical stuff, finally do the email bits

                j = email.userAccountMadeMail(user=sanitizedusername, BCC=True)

                fullname=''
                if user in userfullnamemap:
                    fullname=userfullnamemap[user]
                j = email.addToUAFList(user=user, userfullname=fullname)


            else:


                logger.info ("donothing option set -- not taking any action...")







# feeds subprocess and logs results

def scriptexec(command = [], debug=False, logobj=None):

    if logobj is not None and isinstance(logobj,logging.getLoggerClass()):
        logger=logobj
    else:
        print ("scriptexec called without logobj -- skipping doing:")
        print ("%s" % command)
        return 1

#   sticking this in here for debugging
#    command = ["echo"] + command

    logger.debug("Command Array: %s" % command)

    commandstring = ""

    for a in command:
        commandstring = commandstring + a + " "

    logger.info ("Executing: %s" % commandstring)

    output = ""
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        logger.info("Output: %s" % str(output))
    except subprocess.CalledProcessError as e:
        logger.info("Exec Error: %s" % e.output)
        return 2
    except Exception as e:
        logger.info("Other error: %s" % e)
        return 3


    return 0




if __name__ == '__main__':

#  """
#  Lets get this out of the way in the beginning.  Don't want to screw with the urllib changes
#  pre python2.7, so we just go for python3 off the bat.
#  """
#  if (sys.version_info < (3, 0)):
#      print ("run as: python3 detailsCMSUser.py ...")
#      sys.exit()


    main(sys.argv[1:])
