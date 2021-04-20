cd $CMSSW_BASE/../
tar --exclude-caches-all --exclude-vcs --exclude-caches-all --exclude-vcs -cvzf THBoostedAllHad.tgz CMSSW_11_1_4 --exclude=tmp --exclude=".scram" --exclude=".SCRAM" --exclude=CMSSW_11_1_4/src/timber-env --exclude=CMSSW_11_1_4/src/TH*.root
xrdcp -f THBoostedAllHad.tgz root://cmseos.fnal.gov//store/user/lcorcodi/THBoostedAllHad.tgz
cd $CMSSW_BASE/src/topHBoostedAllHad/