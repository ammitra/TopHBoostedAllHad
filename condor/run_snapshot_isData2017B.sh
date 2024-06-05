#!/bin/bash


############################################################################
# This is a script to perform snapshots on Data only while also marking 
# if the data sample came from run 2017B. Snapshots will be used to detect 
# efficiency of !2017B cut on the total data b/c of different trig effs
############################################################################
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/THBoostedAllHad.tgz ./
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_12_3_5
tar -xzvf THBoostedAllHad.tgz
rm THBoostedAllHad.tgz
rm *.root

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/TopHBoostedAllHad/; cd ../CMSSW_12_3_5/src/
echo 'IN RELEASE'
pwd
ls
eval `scramv1 runtime -sh`
rm -rf timber-env
python3 -m venv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../TopHBoostedAllHad

echo python TEST_DATA_SNAP.py $*
python TEST_DATA_SNAP.py $*

xrdcp -f THsnapshot_*.root root://cmseos.fnal.gov//store/user/ammitra/topHBoostedAllHad/snapshot_data_is2017B/
