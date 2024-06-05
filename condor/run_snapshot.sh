#!/bin/bash
echo "Run script starting"
echo "Running on: `uname -a`"
echo "System software: `cat /etc/redhat-release`"

# Set up pre-compiled CMSSW env
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/THBoostedAllHad.tgz ./
export SCRAM_ARCH=el8_amd64_gcc10
scramv1 project CMSSW CMSSW_12_3_5
echo "Unpacking compiled CMSSW environment tarball..."
tar -xzf THBoostedAllHad.tgz
rm THBoostedAllHad.tgz
mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/TopHBoostedAllHad/; cd ../CMSSW_12_3_5/src/

# CMSREL and virtual env setup
echo 'IN RELEASE'
pwd
ls
echo 'scramv1 runtime -sh'
eval `scramv1 runtime -sh`
echo $CMSSW_BASE "is the CMSSW we have on the local worker node"
rm -rf timber-env
echo 'python3 -m venv timber-env'
python3 -m venv timber-env
echo 'source timber-env/bin/activate'
source timber-env/bin/activate
echo "$(which python3)"

# Set up TIMBER
cd TIMBER
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/cms.cern.ch/el8_amd64_gcc10/external/boost/1.78.0-0d68c45b1e2660f9d21f29f6d0dbe0a0/lib
echo "STARTING TIMBER SETUP......."
source setup.sh
echo "FINISHED TIMBER SETUP......."
cd ../TopHBoostedAllHad

# xrootd debug & certs
#export XRD_LOGLEVEL=Debug
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/

echo python THsnapshot.py $*
python THsnapshot.py $*

xrdcp -f THsnapshot_*.root root://cmseos.fnal.gov//store/user/ammitra/topHBoostedAllHad/snapshot/

