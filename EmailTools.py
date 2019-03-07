"""
Bits and pieces of things useful to deal with emailing users on the LPC
Assuming python3 here

"""


import os
import sys
import re
import logging
import smtplib

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


    def userAccountMadeMail(self, user=""):



        if user == "":
            self.logger.error("User ID: %s got lost -- aborting email!" % user )
            return 1

        useremail = user + '@fnal.gov'

        self.logger.info("Preparing to email %s " % useremail)
        recips = [useremail]
        emailtextstring = "To: %s\n" % useremail
        emailtextstring += "Subject: Welcome to the CMS LPC CAF (Central Analysis Facility)\n"
        recips.append("lpc-support@fnal.gov")
        emailtextstring += "Bcc: lpc-support@fnal.gov\n\n"


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



        FromAddr = "do-not-reply@fnal.gov"
        ToAddr = recips                # this is a list, including Bcc!

        smtpserver = smtplib.SMTP(SMTPSERVER)


        try:
            smtpserver.sendmail(FromAddr, ToAddr, emailtextstring)
        except SMTPException as err:
            self.logger.error("Problem sending email")
            self.logger.error("SMTPException: {0}".format(err))
            return 1

        smtpserver.set_debuglevel(5)
        smtpserver.close()
        self.logger.info("No errors caught -- presumably email has been sent")

        return 0


    def addToUAFList(self, user="", userfullname=""):

        if user == "":
            self.logger.error("User ID: %s got lost -- aborting email!" % user )
            return 1

        if user == "":
            self.logger.error("User full name: %s got lost" % userfullname)
            self.logger.error("replacing with username %s" % user)
            userfullname=user



        useremail = user + '@fnal.gov'


        FromAddr = NEWUSEREMAILSENDER
        ToAddr = "listserv@fnal.gov"

        self.logger.info("Preparing to add %s to UAF list" % useremail)

        emailtextstring = "To: %s\n" % ToAddr
        emailtextstring += "From: %s \n" % FromAddr
        emailtextstring += "Subject: add new user to the list\n\n"
        emailtextstring += "ADD CMS_UAF_USERS %s %s" % (useremail, userfullname)

        try:
            smtpserver.sendmail(FromAddr, ToAddr, emailtextstring)
        except SMTPException as err:
            self.logger.error("Problem sending email")
            self.logger.error("SMTPException: {0}".format(err))
            return 1

        smtpserver.set_debuglevel(5)
        smtpserver.close()
        self.logger.info("No errors caught -- presumably email has been sent")

        return 0


if __name__ == '__main__':

    thingy = EmailTools(debug=True)


    j=thingy.userAccountMadeMail(user="dmason")