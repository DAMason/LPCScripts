"""
Bits and pieces of things useful to deal with emailing users on the LPC
Assuming python3 here

"""


import os
import sys
import re
import pwd
import logging
import smtplib
from optparse import OptionParser


from LPCScriptsConfig import *




class EmailTools:

    def __init__(self, logobj=None, debug=False):

        self.debug=debug

        if logobj is not None and isinstance(logobj,logging.getLoggerClass()):
            self.logger=logobj
        else:
            path, execname = os.path.split(sys.argv[0])
            if len(execname) == 0:
                execname="EmailTools"
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




# bits to send new user email


    def userAccountMadeMail(self, user="", BCC=False):



        if user == "":
            self.logger.error("User ID: %s got lost -- aborting email!" % user )
            return 1

        useremail = user + '@fnal.gov'

        self.logger.info("Preparing to email %s " % useremail)
        recips = [useremail]
        emailtextstring = "To: %s\n" % useremail
        emailtextstring += "Subject: Welcome to the CMS LPC CAF (Central Analysis Facility)\n"
        if BCC and len(NEWUSERBCCLIST) > 0:
            recips.append(NEWUSERBCCLIST)
            emailtextstring += "Bcc: %s\n" % NEWUSERBCCLIST

        emailtextstring += "\n"


        try:
            f = open(NEWUSEREMAILTEXTLOC, 'r')
            for line in f:
                emailtextstring = emailtextstring + line
        except OSError as err:
            self.logger.error("Failing to read new user text file %s" % NEWUSEREMAILTEXTLOC)
            self.logger.error("EMail text string so far: %s" % emailtextstring)
            self.logger.error("OS Error: {0}".format(err))
            return 1

        emailtextstring = emailtextstring % (user)

        self.logger.debug("Email text pulled in: \n%s" % emailtextstring)



        FromAddr = NOREPLYEMAILSENDER
        ToAddr = recips                # this is a list, including Bcc!

        smtpserver = smtplib.SMTP(SMTPSERVER)


        try:
            smtpserver.sendmail(FromAddr, ToAddr, emailtextstring)
        except smtplib.SMTPException as err:
            self.logger.error("Problem sending email")
            self.logger.error("SMTPException: {0}".format(err))
            return 1

        smtpserver.set_debuglevel(5)
        smtpserver.close()
        self.logger.info("No errors caught -- presumably email has been sent")

        return 0




# to add new user to the UAF list

    def addToUAFList(self, user="", userfullname="", quiet=False):

        if user == "":
            self.logger.error("User ID: %s got lost -- aborting email!" % user )
            return 1

        if user == "":
            self.logger.error("User full name: %s got lost" % userfullname)
            self.logger.error("replacing with *")
            userfullname="*"   # supposedly this is an anonymous subscription
                               # also supposedly should never happen



        useremail = user + '@fnal.gov'


        FromAddr = NEWUSEREMAILSENDER
        ToAddr = LISTSERVADDRESS

        self.logger.info("Preparing to add %s to UAF list" % useremail)

        emailtextstring = "To: %s\n" % ToAddr
        emailtextstring += "From: %s \n" % FromAddr
        emailtextstring += "Subject: add new user to the list\n\n"
        if quiet:
            emailtextstring += "QUIET ADD CMS_UAF_USERS %s %s" % (useremail, userfullname)
        else:
            emailtextstring += "ADD CMS_UAF_USERS %s %s" % (useremail, userfullname)

        smtpserver = smtplib.SMTP(SMTPSERVER)



        try:
            smtpserver.sendmail(FromAddr, ToAddr, emailtextstring)
        except smtplib.SMTPException as err:
            self.logger.error("Problem sending email")
            self.logger.error("SMTPException: {0}".format(err))
            return 1

        smtpserver.set_debuglevel(5)
        smtpserver.close()
        self.logger.info("No errors caught -- presumably email has been sent")

        return 0


if __name__ == '__main__':


    """
    Options
    """
    usage = "Usage: %prog [options] thing\n"
    parser = OptionParser(usage=usage)



    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False,
                      help="debug output")

    parser.add_option("-n", "--newuser", action="store", dest="newuser",
                      type="string", default="",
                      help="new user email with username")

    parser.add_option("-u", "--uaf", action="store", dest="uafadd",
                      type="string", default="",
                      help="add user to UAF list")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      default=False,
                      help="UAF addition is quiet")

    helpstring="Bcc new user email to %s" % NEWUSERBCCLIST
    parser.add_option("-b", "--bcc", action="store_true", dest="bcc",
                      default=False,
                      help=helpstring)


    (options,args) = parser.parse_args()




    thingy = EmailTools(debug=options.debug)

    if len(options.newuser)>0:
        print ("doing userAccountMadeMail for user %s" % options.newuser)
        if options.bcc:
            print ("With Bcc to: %s" % NEWUSERBCCLIST)
        j=thingy.userAccountMadeMail(user=options.newuser, BCC=options.bcc)

    if len(options.uafadd)>0:
        print ("doing addToUAFList for user %s" % options.newuser)
        if options.quiet:
            print ("Quietly")

        pwdentry=pwd.getpwnam(options.uafadd)
        fullname=pwdentry[4]   #gecos -- user full name/comment from passwd file
        print ("Full name supposed to be: %s" % fullname)
        j=thingy.addToUAFList(user=options.uafadd,
                              userfullname=fullname,
                              quiet=options.quiet)
