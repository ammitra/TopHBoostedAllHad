cd $CMSSW_BASE/../
tar --exclude-caches-all --exclude-vcs -cvzf THBoostedAllHad.tgz \
    --exclude=tmp --exclude=".scram" --exclude=".SCRAM" \
    --exclude=CMSSW+12_3_5/src/TIMBER/bin/backup_* \
    --exclude=CMSSW_12_3_5/src/timber-env \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/logs \
    --exclude=CMSSW_12_3_5/src/TIMBER/docs \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/plots \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/rootfiles/*.root \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/dataSnapshots \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/dijet_nano/backup* \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/raw_nano/backup* \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/highMassTprime \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/TEST_ddt_12800-125_18.root \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/dijet_nano/NMinus1/*.root \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/DDTMaps_Run2018UL.root  \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/GenParticleTesting \
    --exclude=CMSSW_12_3_5/src/TopHBoostedAllHad/ParticleNetSFs/EfficiencyMaps/*.root \
    CMSSW_12_3_5

xrdcp -f THBoostedAllHad.tgz root://cmseos.fnal.gov//store/user/$USER/THBoostedAllHad.tgz
cd $CMSSW_BASE/src/TopHBoostedAllHad/
