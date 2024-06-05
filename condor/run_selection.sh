#!/bin/bash
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/THBoostedAllHad.tgz ./
scramv1 project CMSSW CMSSW_12_3_5
tar -xzvf THBoostedAllHad.tgz
rm THBoostedAllHad.tgz
rm *.root

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/PostAPV/TopHBoostedAllHad/; cd ../CMSSW_12_3_5/src/
echo 'IN RELEASE'
pwd
ls
eval `scramv1 runtime -sh`
cd PostAPV/
#rm -rf timber-env
python3 -m venv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../TopHBoostedAllHad

echo python THselection.py $*
python THselection.py $*

xrdcp -f rootfiles/THselection_*.root root://cmseos.fnal.gov//store/user/ammitra/topHBoostedAllHad/selection/

