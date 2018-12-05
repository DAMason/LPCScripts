Attempt to gather together some of the replacement vulcan scripts.



Currently two file generators -- one to make gridmaps needed for EOS, and another to make
CERN uid lists for CRAB coming into the LPC.

Needs python3

To set up:

LPCScriptsConfig.py  has some necessary variables, including location of certificate
                     needed to call up VOMS server.  (HOSTCERT and HOSTKEY vars)
                     also has the FERRY host URL, and VOMS host URL.

generateGridMap.py:

$ python3 generateGridMap.py -h
Usage: generateGridMap.py [options] thing


Options:
  -h, --help            show this help message and exit
  -s HOSTURL, --server=HOSTURL
                        FERRY Server host URL
  -p CAPATH, --capath=CAPATH
                        CA Path
  -c CERT, --cert=CERT  full path to cert
  -d, --debug           debug output
  -o OUTPUTFILE, --output=OUTPUTFILE
                        output file
  -i INPUTFILE, --input=INPUTFILE
                        input file for hardwired gridmaps


options can override settings in LPCScriptsConfig.py


python3 generateGridMap.py    will:

make a log dir and start logging in there
if successful will make a grid-mapfile with all the LPC users in there and their DN's.

each following execution -- if successful updates grid-mapfile, backing up the old one
with a timestamp in the log dir

running this with -d essentially dumps all outputs into log file and console.


This NEEDS to have grid-mapfile-hardwires in there to ensure things like SAM tests and
PhEDEx transfers continue to work.

Failures should leave the original grid-mapfile untouched



generateCERNUIDList.py:

similar to the gridmap generator, but cooks up a list of CERN uid's, as well as a mapping
(default CERNuids, CERNuids.map).  Its just translating FERRY outputs, doesn't need
to contact other things


FERRYTools.py, VOMSTools.py   Just some REST translation bits and pieces.

