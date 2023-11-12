import ROOT
import glob
from array import array
import numpy as np
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
import subprocess

#mPhi = OrderedDict([(i,None) for i in [75,100,125,175,200,250,350,450,500]])
mTP = OrderedDict([(i,None) for i in range(800,3100,100) if i not in [2100,2200,2300,2500,2600,2700]])

redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/ammitra/topHBoostedAllHad/selection'

def GetEfficiencies(year):
    #efficiencies = OrderedDict([(i,mPhi.copy()) for i in range(800,3100,100) if i not in [2100,2200,2300,2500,2600,2700]])
    efficiencies = OrderedDict([(i, mTP.copy()) for i in [75,100,125,175,200,250,350,450,500]])
    selection_files_str = subprocess.check_output('xrdfs {} ls -u {} | grep Tprime | grep {}.root'.format(redirector,eos_path,year), shell=True)
    selection_files = selection_files_str.split()
    print('There are {} nominal selection files for {}'.format(len(selection_files),year))
    for selection in selection_files:
	mTprime = int(selection.split('/')[-1].split('.')[0].split('_')[2].split('-')[1])
	mphi    = int(selection.split('/')[-1].split('.')[0].split('_')[2].split('-')[2])
	print('processing ({},{})'.format(mTprime,mphi))
	f = ROOT.TFile.Open(selection,'READ')
	h = f.Get('cutflow')
        start = h.GetBinContent(5) # preselection
        end   = h.GetBinContent(8) # final cut on tight Hbb (SR pass)
	if start == 0.0:
            print('\t start: {}\tend: {}'.format(start,end))
            eff = 0.0
        else:
            eff = end/start
        efficiencies[mphi][mTprime] = eff
        f.Close()

    effArr = np.zeros((9,17),dtype=float)
    col = 0 # columns are fixed phi mass
    for mtprime, mphis in efficiencies.items():
        row = len(mphis)-1 # rows are fixed Tprime mass
        for mphi, eff in mphis.items():
            if row < 0: continue
            if eff == None: eff = 0.0
            effArr[col][row] = eff
            print('row: {}\ncol: {}\neff: {}\nMX: {}\nMY: {}\n'.format(row,col,eff,mtprime,mphi))
            row -= 1
        col += 1

    fig, ax = plt.subplots(figsize=(15,15))
    im = ax.imshow(100.*effArr.T)

    ymasses = [str(i) for i in range(800,3100,100) if i not in [2100,2200,2300,2500,2600,2700]]
    xmasses = [str(i) for i in [75,100,125,175,200,250,350,450,500]]
    ymasses.reverse()

    ax.set_xticks(np.arange(len(xmasses)))
    ax.set_xticklabels(xmasses)
    ax.set_yticks(np.arange(len(ymasses)))
    ax.set_yticklabels(ymasses)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(len(xmasses)):
        for j in range(len(ymasses)):
            efficiency = round(effArr[i, j]*100.,1)
            if efficiency == 0.0: continue
            if efficiency < 70.:
                textcolor='white'
            else:
                textcolor='grey'
            text = ax.text(i, j, '{}%'.format(round(effArr[i, j]*100.,1)),ha="center", va="center", color=textcolor, fontsize='small', rotation=45, rotation_mode='anchor')

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Signal Efficiency (%)', rotation=-90, va="bottom",fontsize='large')
    ax.set_title("Signal Efficiency after selection, 20{}".format(year))
    ax.set_aspect('auto')
    plt.xlabel(r"$m_{\phi}$ [GeV]",fontsize='large')
    plt.ylabel(r"$m_{t\phi}$ [GeV]",fontsize='large')
    plt.savefig('plots/sigEff2D_selection_{}.png'.format(year),dpi=300)

if __name__ == "__main__":
    for year in ['16','16APV','17','18']:
        GetEfficiencies(year)
