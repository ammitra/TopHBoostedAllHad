'''
Combines rootfiles from CR+SR and ttbarCR into a single root file for 2DAlphabet.
Only Data, ttbar, and Signal processes are in ttbarCR, so these are the only processes 
which must be combined.
'''
from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

def CombineCommonSets(HT='750', signal='TprimeB-1800-125', dryRun=True):
    # 0 = HT
    # 1 = ttbarCR_
    # 2 = process
    # 3 = year
    # 4 = syst_up/down
    baseStr = 'rootfiles/THselection_HT{0}_{1}{2}_{3}{4}.root'
    for proc in ['ttbar',signal]:
	for y in ['16','16APV','17','18']:
	    for syst in ['JER','JES','JMR','JMS']:
		for var in ['up','down']:
		    if dryRun:
			print('rootcp %s:* %s'%(
			    baseStr.format(HT, 'ttbarCR_', proc, y, '_'+syst+'_'+var),
			    baseStr.format(HT, '', proc, y, '_'+syst+'_'+var))
			)
		    else:
			ExecuteCmd(
			    'rootcp %s:* %s'%(
				baseStr.format(HT, 'ttbarCR_', proc, y, '_'+syst+'_'+var),
				baseStr.format(HT, '', proc, y, '_'+syst+'_'+var))
			)
	    # now do no variations
	    if dryRun:
		print('rootcp %s:* %s'%(
		    baseStr.format(HT, 'ttbarCR_', proc, y, ''),
		    baseStr.format(HT, '', proc, y, ''))
		)
	    else:
		ExecuteCmd('rootcp %s:* %s'%(
                    baseStr.format(HT, 'ttbarCR_', proc, y, ''),
                    baseStr.format(HT, '', proc, y, ''))
                )

    # do data separately
    if dryRun:
	print('rootcp rootfiles/THselection_HT750_ttbarCR_Data_Run2.root:* rootfiles/THselection_HT750_Data_Run2.root')
    else:
	ExecuteCmd('rootcp rootfiles/THselection_HT750_ttbarCR_Data_Run2.root:* rootfiles/THselection_HT750_Data_Run2.root')

if __name__ == "__main__":
    CombineCommonSets(HT='750', signal='TprimeB-1800-125', dryRun=False)
