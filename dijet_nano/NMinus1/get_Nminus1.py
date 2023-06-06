from glob import glob
import subprocess, os

from TIMBER.Tools.Common import ExecuteCmd
redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/ammitra/topHBoostedAllHad/NMinus1/'

files = subprocess.check_output('eos root://cmseos.fnal.gov ls %s'%(eos_path), shell=True)
for f in files.split('\n'):
    ExecuteCmd('xrdcp {}{}{} dijet_nano/NMinus1/'.format(redirector, eos_path, f))
