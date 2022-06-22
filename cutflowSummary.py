'''
Cutflow information is stored differently in snapshots and selection files. 
Snapshots: stored in Events TTree
	NPROC, NFLAGS, NJETS, NPT, NKIN
Selection: stored in Histogram
	nTop_CR, nTop_SR
	higgsF_{}, higgsL_{}, higgsP_{}
'''
import ROOT
import glob, os
from argparse import ArgumentParser
from collections import OrderedDict
import numpy as np

def generateCutflow(setName):
    '''
	main function to generate the cutflow from both snapshot and selection for a set
    '''
    # first do snapshots
    snapVars = OrderedDict([('NPROC',0.),('NFLAGS',0.),('NJETS',0.),('NPT',0.),('NKIN',0.),('nTop_CR',0.),('higgsF_CR',0.),('higgsL_CR',0.),('higgsP_CR',0.),('nTop_SR',0.),('higgsF_SR',0.),('higgsL_SR',0.),('higgsP_SR',0.)])
    years = OrderedDict([('16',snapVars.copy()), ('16APV', snapVars.copy()), ('17', snapVars.copy()), ('18', snapVars.copy())])
    for year, varDict in years.items():
	#if not os.path.exists('dijet_nano/{}_{}_snapshot.txt'.format(setName,year)):
	    #pass
	fileList = glob.glob('dijet_nano/{}*_{}_snapshot.txt'.format(setName,year))
        for snapFile in fileList:
       	    # need to get names of ROOT files from txt
	    fList = open(snapFile)
	    rFiles = [i.strip() for i in fList if i != '']
	    for fName in rFiles:
	        #print('opening {}'.format(fName))
	        f = ROOT.TFile.Open(fName, 'READ')
	        # check for empty TTrees
	        if not f.Get('Events'):
		    #print('Skipping file due to no Events TTree:\n\t{}'.format(fName))
		    continue
	        e = f.Get('Events')
	        if not e.GetEntry():
		    #print('Skipping file due to empty Events TTree:\n\t{}'.format(fName))
		    continue
		e.GetEntry()	# initialize all branches
	        for cut, num in varDict.items():
		    if ('SR' in cut) or ('CR' in cut):
		        pass		    
		    else:
	                varDict[cut] += e.GetLeaf(cut).GetValue(0)
	        f.Close()

    # selection will have common sets joined by default (see rootfiles/get_all.py and perform_selection.py)
    # i.e.: 	THselection_ZJets_18.root
    for year, varDict in years.items():
	if not os.path.exists('rootfiles/THselection_{}_{}.root'.format(setName, year)):
	    pass
	f = ROOT.TFile.Open('rootfiles/THselection_{}_{}.root'.format(setName, year))
	h = f.Get('cutflow')
	for i in range(1, 9):	# cutflow has 8 bins w the cuts, starting from index 1
	    var = h.GetXaxis().GetBinLabel(i)
	    val = h.GetBinContent(i)
	    varDict[var] += val
	f.Close()

    # returns dict of {year: cutflowDict}
    return years


# now make latex table
labels = ["Sample","nProc","nFlags","nJets","p_{t}","nKin","CR_topCut","CR_F","CR_L","CR_P","SR_topCut","SR_F","SR_L","SR_P"]

sets = ["ttbar", "QCD", "WJets", "ZJets", "Data"]

for s in sets:
    res = generateCutflow(s)

    print('\n------------------ {} -------------------'.format(s))
    for year, dicts in res.items():
	print('----------------- {} -----------------'.format('20'+year))
	latexRow = s + " &"
	for var, val in dicts.items():
	    if (val > 10000):
		latexRow += " {0:1.2e} &".format(val)
	    else:
		latexRow += " {0:.3f} &".format(val)
        print(" & ".join(labels)+" \\\\")
        print(latexRow)

'''
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
			action='store', required=True,
			help='ttbar, QCD, WJets, ZJets, Data')

    args = parser.parse_args()
    print('Performing cutflow for {}'.format(args.setname))
    res = generateCutflow(args.setname)
    print('------------------ {} -------------------'.format(args.setname))
    for year, dicts in res.items():
	print('----------------- {} -----------------'.format('20'+year))
	for var, val in dicts.items():
	    print('{} : {}'.format(var, val))
'''
