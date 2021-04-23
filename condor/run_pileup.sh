#!/bin/bash
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/lcorcodi/THBoostedAllHad.tgz ./
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_11_1_4
tar -xzvf THBoostedAllHad.tgz
rm THBoostedAllHad.tgz
rm *.root

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_11_1_4/src/topHBoostedAllHad/; cd ../CMSSW_11_1_4/src/
echo 'IN RELEASE'
pwd
ls
eval `scramv1 runtime -sh`
rm -rf timber-env
python -m virtualenv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../topHBoostedAllHad

echo python THpileup.py $*
python THpileup.py $*

xrdcp -f THpileup_*.root root://cmseos.fnal.gov//store/user/lcorcodi/topHBoostedAllHad/pileup/

