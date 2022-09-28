'''
Compares the PNet shape uncertainties on the 1800-125 signal
'''

import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array

baseStr = 'THselection_TprimeB-1800-125_18'
histStr = 'MthvMh_particleNet_SR_pass__nominal'

colors = ["black","blue","red"]

histsX = []
edgesX = []
yrangesX = []

histsY = []
edgesY = []
yrangesY = []

labels = []

for var in ['nom','_PNet_up','_PNet_down']:
    f = ROOT.TFile.Open('{0}{1}.root'.format(baseStr,var if 'nom' not in var else ''),'OPEN')
    # hist we will analyze
    h = f.Get(histStr)
    hX = h.ProjectionX('TprimeB-1800-125_{}_projX'.format(var),1,-1)
    yrangesX.append(hX.GetMaximum())
    histX, edgeX = hist2array(hX,return_edges=True)
    histsX.append(histX)
    edgesX.append(edgeX)

    hY = h.ProjectionY('TprimeB-1800-125_{}_projY'.format(var),1,-1)
    yrangesY.append(hY.GetMaximum())
    histY, edgeY = hist2array(hY,return_edges=True)
    histsY.append(histY)
    edgesY.append(edgeY)

    labels.append('TprimeB-1800-125 {}'.format(var))
    f.Close()

for proj in ['x', 'y']:
    yTitle = 'Events/{} GeV'.format(5 if proj=='x' else 100)
    xTitle = '$M_{%s}$ [GeV]'%('\phi' if proj=='x' else 't\phi')

    plt.style.use([hep.style.CMS])
    fig, ax = plt.subplots()
    if proj == 'x':
        for i, h in enumerate(histsX):
            hep.histplot(h,edgesX[i][0],stack=False,ax=ax,label=labels[i],linewidth=3,zorder=2,color=colors[i])
    else:
        for i, h in enumerate(histsY):
            hep.histplot(h,edgesY[i][0],stack=False,ax=ax,label=labels[i],linewidth=3,zorder=2,color=colors[i])

    ax.legend()
    ax.set_ylabel(xTitle)
    ax.set_xlabel(yTitle)
    plt.xlabel(xTitle, horizontalalignment='right', x=1.0)
    plt.ylabel(yTitle,horizontalalignment='right', y=1.0)
    if proj=='x':
        ax.set_ylim([0.,max(yrangesX)*1.25])
    else:
        ax.set_ylim([0.,max(yrangesY)*1.25])
    hep.cms.text("WiP",loc=1)
    plt.legend(loc='best',ncol=1)#loc = 'best'

    outFile = 'PNetShapeUnc_{}-proj.pdf'.format(proj)
    plt.savefig(outFile)
    plt.savefig(outFile.replace("pdf","png"))
    plt.clf()

