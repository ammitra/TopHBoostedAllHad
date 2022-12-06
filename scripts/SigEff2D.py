import ROOT
import glob
from array import array
import numpy as np
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
'''
Generates 2D plots (m_phi vs m_tphi) of the final signal efficiencies.
'''

def _addFile(TChain, f):
    '''Add file to TChains being tracked.
    Args:
        f (str): File to add.
    '''
    if f.endswith(".root"): 
        if 'root://' not in f and f.startswith('/store/'):
            f='root://cms-xrd-global.cern.ch/'+f
        if ROOT.TFile.Open(f,'READ') == None:
            raise ReferenceError('File %s does not exist'%f)
        tempF = ROOT.TFile.Open(f,'READ')
        if tempF.Get('Events') != None:
            TChain.Add(f)
        tempF.Close()
    elif f.endswith(".txt"): 
        txt_file = open(f,"r")
        for l in txt_file.readlines():
	    print('ROOT file: {}'.format(l))
            thisfile = l.strip()
            _addFile(TChain, thisfile)
    else:
        raise Exception("File name extension not supported. Please provide a single or list of .root files or a .txt file with a line-separated list of .root files to chain together.")
    

mPhi = OrderedDict([(i,None) for i in [75,100,125,175,200,250,350,450,500]])

def GetEfficiencies(year):
    '''year (str): 16, 16APV, 17, 18'''
    # Create the TPrime mass dict, with each TPrime mass point having a copy of the mPhi dict
    #efficiencies = {TMass:mPhi.copy() for TMass in range(800,1900,100)}
    efficiencies = OrderedDict([(i,mPhi.copy()) for i in range(800,1900,100)])
    # Get the actual snapshots for a given year
    snapshots = glob.glob('dijet_nano/TprimeB-*_{}_snapshot.txt'.format(year))
    # Loop through the snapshots and create a TChain for each
    for snapshot in snapshots:
	print('Opening: {}'.format(snapshot))
	TMass = int(snapshot.split('/')[-1].split('_')[0].split('-')[1])
	PhiMass = int(snapshot.split('/')[-1].split('_')[0].split('-')[2])
	TChain = ROOT.TChain('Events')
	_addFile(TChain, snapshot)
	# put everything in memory
	TChain.GetEntry()
	start = TChain.GetLeaf('NPROC').GetValue(0)
	end = TChain.GetLeaf('NKIN').GetValue(0)
	eff = end/start
	efficiencies[TMass][PhiMass] = eff

    effArr = np.zeros((11,9),dtype=float)
    row = 11
    for TMass, PhiMasses in efficiencies.items():
	col = 0
	row -= 1
	for PhiMass, eff in PhiMasses.items():
	    if eff==None: eff = 0.0
	    effArr[row][col] = eff
	    col += 1	    
    print(effArr)
    
    fig, ax = plt.subplots(figsize=(10,10))
    im = ax.imshow(100.*effArr)
    TMasses = [str(i) for i in range(800,1900,100)]
    TMasses.reverse()
    PhiMasses = [str(i) for i in [75,100,125,175,200,250,350,450,500]]
    ax.set_xticks(np.arange(len(PhiMasses)))
    ax.set_xticklabels(PhiMasses)
    ax.set_yticks(np.arange(len(TMasses)))
    ax.set_yticklabels(TMasses)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    for i in range(len(TMasses)):
	for j in range(len(PhiMasses)):
	    text = ax.text(j, i, '{}%'.format(round(effArr[i, j]*100.,1)),ha="center", va="center", color="w", fontsize='medium')
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Signal Efficiency (%)', rotation=-90, va="bottom",fontsize='large')
    ax.set_title("Signal Efficiency 20{}".format(year))
    plt.xlabel(r"$m_{\phi}$ [GeV]",fontsize='large')
    plt.ylabel(r"$m_{t\phi}$ [GeV]",fontsize='large')
    plt.savefig('plots/SignalEfficiency_{}.png'.format(year),dpi=300)

    '''
    # Now that we have all the efficiencies, plot them 
    y = array('d',[800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800])
    x = array('d',[75,100,125,175,200,250,350,450,500])
    hist = ROOT.TH2D("Eff2D_{}".format(year),"",8,x,10,y)
    hist.SetStats(0)
    hist.GetXaxis().SetTitle('m_{#phi} [GeV]')
    hist.GetYaxis().SetTitle('m_{t#phi} [GeV]')
    for TMass, PhiMasses in efficiencies.items():
	for PhiMass, eff in PhiMasses.items():
	    xBin = hist.GetXaxis().FindBin(PhiMass)
	    yBin = hist.GetYaxis().FindBin(TMass)
	    if (TMass==1800) and (PhiMass==125): print('{}-{} efficiency: {}'.format(TMass, PhiMass, round(eff*100.,3)))
	    if eff == None:
		eff = 0.0
	    hist.SetBinContent(xBin, yBin, round(eff*100.,3))
    can = ROOT.TCanvas('c','c',1000,800)
    hist.Draw('colz text')
    can.SaveAs('plots/SignalEfficiency_{}.pdf'.format(year))
    print(efficiencies)
    '''

if __name__=='__main__':
    for year in ['16','16APV','17','18']:
	GetEfficiencies(year)
	    
