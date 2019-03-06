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

        emailtextstring=""

        try:
            f = open(NEWUSEREMAILTEXTLOC, 'r')
            for line in f:
                emailtextstring = emailtextstring + line
        except OSError as err:
            self.logger.error("Failing to read new user text file %s" % NEWUSEREMAILTEXTLOC)
            self.logger.error("EMail text string so far: %s" % emailtextstring)
            self.logger.error("OS Error: {0}".format(err))
            return 1

        self.logger.debug("Email text pulled in: \n %s" % emailtextstring)

        useremail = user + '@fnal.gov'

        self.logger.debug("Preparing to email %s " % useremail)

        FromAddr = NEWUSEREMAILSENDER
        ToAddr = useremail

        smtpserver = smtplib.SMTP(SMTPSERVER)

        try:
            smtpserver.sendmail(FromAddr, ToAddr, emailtextstring)
        except:
            self.logger.error("Problem sending email")



        smtpserver.set_debuglevel(5)
        smtpserver.close()

        return 0






if __name__ == '__main__':

    thingy = EmailTools(debug=True)


    j=thingy.userAccountMadeMail(user="dmason")