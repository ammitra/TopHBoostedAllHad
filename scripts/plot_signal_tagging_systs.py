'''
Script to plot the signal distribution under variations of the tagging systematics
'''
import matplotlib
matplotlib.use('Agg')

import ROOT as r
from optparse import OptionParser
from time import sleep
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
import ctypes
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os 


def plotSigTemplates(outFile,variations,xTitle="",yTitle="",yRange=[],xRange=[],log=True,rebinX=1,luminosity="36.3",projection="",slices=[0,-1],normalize=False):
    histos  = []
    labels  = []
    #variations = ['','PNetTop_up','PNetTop_down']#,'PNetXbb_up','PNetXbb_down']
    linestyles = ["solid","dashed","dashed"]#"dotted","dotted","dashed","dashed"]

    for variation in variations:
        tempFile = r.TFile.Open('rootfiles/THselection_HT750_TprimeB-1800-125_18{}.root'.format(variation if variation == '' else '_'+variation))
        h = tempFile.Get('MHvMTH_SR_pass__nominal')

        if normalize:
            h.Scale(1./h.Integral())

        if(projection=="x"):
            h = h.ProjectionX(h.GetName()+"_x",slices[0],slices[1])
        elif(projection=="y"):
            h = h.ProjectionY(h.GetName()+"_y",slices[0],slices[1])

        h.RebinX(rebinX)
        hist, edges = hist2array(h,return_edges=True)
        histos.append(hist)
        labels.append(variation)

    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()
    plt.sca(ax)

    #--------------------------#
    hep.histplot(histos,edges[0],stack=False,ax=ax,label=labels,linestyle=linestyles,linewidth=3,histtype="step")
    if(log):
        ax.set_yscale("log")
    ax.legend()
    ax.set_ylabel(yTitle)
    ax.set_xlabel(xTitle)
    plt.ylabel(yTitle,horizontalalignment='right', y=1.0)
    
    if(yRange):
        ax.set_ylim(yRange)
    else:
        ax.set_ylim([None,max(histos[1])*1.5])
    if(xRange):
        ax.set_xlim(xRange)
    if(luminosity):
        lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
        hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    plt.legend(loc="best",ncol=2,handletextpad=0.3)#loc = 'best'
    
    plt.tight_layout()
    print("Saving {0}".format(outFile))
    plt.savefig(outFile)
    plt.savefig(outFile.replace(".png",".pdf"))
    plt.cla()
    plt.clf()
    tempFile.Close()

if __name__ == "__main__":
    for proj in ['x','y']:
        plotSigTemplates(
        outFile=f'plots/signal_tagging_systs_PNetXbb_{proj}.png',
        variations=['','PNetXbb_up','PNetXbb_down'],
        xTitle=r"$m_\phi$" if proj == 'x' else r'$m_{t\phi}$',
        yTitle="Events",
        yRange=[],
        xRange=[],
        log=False,
        rebinX=1,
        luminosity="36.3",
        projection=proj,
        slices=[0,-1],
        normalize=False
        )
