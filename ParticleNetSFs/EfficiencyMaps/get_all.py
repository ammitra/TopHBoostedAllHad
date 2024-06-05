'''
Gathers all efficiency maps from the EOS and dumps it into the ParticleNetSFs/EfficiencyMaps/ directory
'''
from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/ammitra/topHBoostedAllHad/TaggerEfficiencies/'

rawFiles = subprocess.check_output('eos %s ls %s'%(redirector,eos_path), shell=True, text=True)
files = rawFiles.split('\n')

for fName in files:
    if (fName == ''):
        pass
    else:
        ExecuteCmd('xrdcp -f %s%s%s ParticleNetSFs/EfficiencyMaps/'%(redirector,eos_path,fName))

