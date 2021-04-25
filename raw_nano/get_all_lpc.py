from TIMBER.Tools.Common import ExecuteCmd
import sys
das = {
    "16": {
        # "TprimeT": "/TprimeTToTH_M-MASS_LH_TuneCUETP8M1_13TeV-madgraph-pythia8/RunIISummer16NanoAODv7-PUMoriond17_Nano02Apr2020_102X_mcRun2_asymptotic_v8-v1/NANOAODSIM",
        "TprimeB": "/TprimeBToTH_M-MASS_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
        "DataB1": "/JetHT/Run2016B-ver1_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataB2": "/JetHT/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataC": "/JetHT/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataD": "/JetHT/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataE": "/JetHT/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataF": "/JetHT/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD",
        "DataG": "/JetHT/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataH": "/JetHT/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    },
    "17": {
        # "TprimeT": "/TprimeTToTH_M-MASS_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "TprimeB": "/TprimeBToTH_M-MASS_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
        "DataB": "/JetHT/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataC": "/JetHT/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataD": "/JetHT/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataE": "/JetHT/Run2017E-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataF": "/JetHT/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD"
    },
    "18": {
        # "TprimeT": "/TprimeTToTH_M-MASS_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "TprimeB": "/TprimeBToTH_M-MASS_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
        "DataA": "/JetHT/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataB": "/JetHT/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataC": "/JetHT/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
        "DataD": "/JetHT/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD"
    }
}

def GetFiles(das_name,setname,year):
    ExecuteCmd('dasgoclient -query "file dataset=%s" > %s_%s_temp.txt'%(das_name,setname,year),'dryrun' in sys.argv)
    f = open('%s_%s_temp.txt'%(setname,year),'r')
    fout = open('%s_%s.txt'%(setname,year),'w')
    for l in f.readlines():
        fout.write('root://cmsxrootd.fnal.gov/'+l)
    f.close()
    fout.close()
    if 'dryrun' not in sys.argv:
        ExecuteCmd('rm %s_%s_temp.txt'%(setname,year),'dryrun' in sys.argv)

latex_lines = {"16":[],"17":[],"18":[]}
for year in das.keys():
    for setname in das[year].keys():
        if 'Tprime' in setname:
            for mass in range(800,1900,100):
                das_name = das[year][setname].replace('MASS',str(mass))
                setname_mod = setname + '-' + str(mass)
                GetFiles(das_name,setname_mod,year)
                latex_lines[year].append('| %s | %s |'%(setname_mod.replace('-', ' ')+' GeV',das_name))
        else:
            GetFiles(das[year][setname],setname,year)
            latex_lines[year].append('| %s | %s |'%(setname,das[year][setname]))
            
for y in sorted(latex_lines.keys()):
    print ('\n20%s'%y)
    print ('| Setname | DAS location |')
    print ('|---------|--------------|')
    for l in latex_lines[y]: print (l)