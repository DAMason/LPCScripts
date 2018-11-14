#!/user/bin/env python3

"""
Configuration options for the LPC scripts
"""



# Ferry host URL
FERRYHOSTURL = "https://fermicloud033.fnal.gov:8443"


# CERN VOMS URL
VOMSHOSTURL = "https://voms2.cern.ch:8443"

# Host cert and key locations
HOSTCERT = "/etc/grid-security/hostcert.pem"
HOSTKEY = "/etc/grid-security/hostkey.pem"


# CA path
CAPATH = "/etc/grid-security/certificates"

# default storage resource
DEFAULTSTORAGERESOURCE = "lpcinteractive"

# pool username to map non FNAL users too
CMSDEFAULTPOOLUSER = "cms-crab-user"

# supplemental gridmap for special DN mappings
HARDWIREDGRIDMAP = "grid-mapfile-hardwires"