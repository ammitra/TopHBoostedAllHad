'''
Plot the event overlap b/w ttbarCR and SR for data, some signals, and ttbar MC
Adapted from Matej Roguljic: 
    https://github.com/mroguljic/X_YH_4b/blob/UL/misc/scatterPNet.py
Plots will be of the form (Xbb score, DeepAK8)
'''
import matplotlib
matplotlib.use('Agg')

import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
#import mplhep as hep
from root_numpy import hist2array
from root_numpy import tree2array
import matplotlib.patches as patches
from math import log10
from matplotlib.ticker import FuncFormatter

def transform(x):
    res = -log10(1-x/1.02)
    return res
 
def revert(x):
    res = 1.02*(1.-10**(-x))
    return res

def tickFunc(x,pos):
    newtickLabel = revert(x)
    return "{0}".format(newtickLabel)

def CornersToArguments(x1,y1,x2,y2):
    #returns arguments for patches.Rectangle in transformed axis
        corner = (transform(x1),transform(y1))
        width = transform(x2) - transform(x1)
        height  = transform(y2) - transform(y1)
        return corner,width,height

def makePlot(year, outputFile, signal='1800-125', siglabel='$m_T{^\prime}$=1800, $m_{\phi}$=125 GeV'):
    '''Compare the overlap b/w ttbar and signal events 
    Args:
	year 	   (str): 16/16APV/17/18
	outputFile (str): name of output plot
	signal     (str): signal to plot
    '''
    XbbTagger = 'particleNetMD_HbbvsQCD'
    TopTagger = 'deepTagMD_TvsQCD'
    filePrefix = 'rootfiles/ttbarCR_vs_SR_overlap_HT750_{}_%s.root'%(year)

    TTstop = 1800
    sigstop = 200

    # First get the ttbar for this year 
    ttFile = ROOT.TFile.Open(filePrefix.format('ttbar'),'READ')
    ttEvts = ttFile.Get('Events')
    ttPNet = tree2array(ttEvts, branches=['-log10(1-(Higgs_{}/1.02))'.format(XbbTagger)], stop=TTstop)
    ttPNet = ttPNet.astype(np.float)
    ttDAK8 = tree2array(ttEvts, branches=['-log10(1-(Higgs_{}/1.02))'.format(TopTagger)], stop=TTstop)
    ttDAK8 = ttDAK8.astype(np.float)

    # Now get the signal for this year
    sigFile = ROOT.TFile.Open(filePrefix.format('TprimeB-'+signal),'READ')
    sigEvts = sigFile.Get('Events')
    sigPNet = tree2array(sigEvts, branches=['-log10(1-(Higgs_{}/1.02))'.format(XbbTagger)], stop=sigstop)
    sigPNet = sigPNet.astype(np.float)
    sigDAK8 = tree2array(sigEvts, branches=['-log10(1-(Higgs_{}/1.02))'.format(TopTagger)], stop=sigstop)
    sigDAK8 = sigDAK8.astype(np.float)

    # Plotting setup
    matplotlib.rcParams.update({'font.size': 28})
    f, ax = plt.subplots(figsize=(10,10))
    plt.sca(ax)

    # Plot the ttbar and signal events
    plt.scatter(sigPNet, sigDAK8, marker='s', facecolors='darkslategray', edgecolors='darkslategray', label=siglabel)
    plt.scatter(ttPNet, ttDAK8, marker='o', facecolors='none', edgecolors='red', alpha=0.4, label=r'$t\bar{t}$')

    # Format axes
    plt.xlabel('$\phi$-candidate ParticleNet Xbb score', horizontalalignment='right', x=1.0)
    plt.ylabel('$\phi$-candidate DeepAK8MD Top score', horizontalalignment='right', y=1.0)
    scoreMax = 1.0
    ax.set_ylim([0,transform(scoreMax)])
    ax.set_xlim([0,transform(scoreMax)])

    if '16' in year:
	DAK8_WP = 0.889
    elif year == '17':
	DAK8_WP = 0.863
    else:
	DAK8_WP = 0.92

    # Create vertical lines for the SR F/L/P delineations and horizontal for ttbarCR
    SR_LT_coords = np.array([transform(0.8),transform(0.98)])
    TT_FP_coords = transform(DAK8_WP)

    ax.vlines(SR_LT_coords, 0, transform(scoreMax), linestyles='dashed', )
    ax.hlines(TT_FP_coords, 0, transform(scoreMax), linestyles='dashed')

    ax.legend(loc='upper left', bbox_to_anchor=(0.0, 1.25), ncol=2, fancybox=True, shadow=True, fontsize=28)

    xticks = [0.0, 0.8, 0.98, scoreMax]
    yticks = [0.0, DAK8_WP, scoreMax]
    transf_xticks = np.array([transform(x) for x in xticks])
    transf_yticks = np.array([transform(y) for y in yticks])
    plt.xticks(transf_xticks)
    plt.yticks(transf_yticks)

    formatter = FuncFormatter(tickFunc)
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.minorticks_off()

    ax.title.set_text('SR vs ttbarCR overlap 20{}'.format(year))

    plt.savefig("%s.png"%outputFile, bbox_inches='tight')


if __name__ == "__main__":
    for year in ['16','16APV','17','18']:
	makePlot(year=year, outputFile='plots/ttbarCR_SR_overlap_%s'%year, signal='1800-125', siglabel='$m_T{^\prime}$=1800, $m_{\phi}$=125 GeV')
