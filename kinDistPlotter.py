'''
utility for plotting kinematic distributions per year. 
First run python THdistributions.py -y <year> to make the proper distribution files, then run this with the same flag. 

NOTE: This only runs on python 3. 
'''

import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
from glob import glob

# var : (xtitle, ytitle)
varnames = {
    'pt0': (r'Leading AK8 jet $p_{T}$', r'Events/20 GeV'),
    'pt1': (r'Sublead AK8 jet $p_{T}$', r'Events/20 GeV'),
    'HT': (r'Sum of lead and sublead jet $p_{T}$', r'Events/20 GeV'),
    'eta0': (r'Leading AK8 jet $\eta$',r'Events/10'),
    'eta1': (r'Sublead AK8 jet $\eta$',r'Events/10'),
    'phi0': (r'Leading AK8 jet $\varphi$',r'Events/10'),
    'phi1': (r'Sublead AK8 jet $\varphi$',r'Events/10')   
}


def plot(var,year,xtitle,ytitle):
    '''
    var (str)    = variable to plot
    year (str)   = year to plot
    xtitle (str) = title for x axis
    ytitle (str) = title for y axis

    '''
    histosBkg = []
    edgesBkg = []
    labelsBkg = []
    colorsBkg = []

    histosData = []
    edgesData = []
    labelsData = []
    colorsData = []

    for name in ['Data','QCD','VJets','ttbar']:
        tempFile = ROOT.TFile.Open('rootfiles/kinDist_{}_{}.root'.format(name, year))
        h = tempFile.Get(var)
        if name == 'Data':
            hist, edges = hist2array(h, return_edges=True)
            histosData.append(hist)
            edgesData.append(edges[0])
            labelsData.append('Data')
            colorsData.append('k')
        else:
            hist, edges = hist2array(h, return_edges=True)
            histosBkg.append(hist)
            edgesBkg.append(edges[0])
            if name == 'QCD':
                labelsBkg.append('Multijets')
                colorsBkg.append('y')
            elif name == 'V':
                labelsBkg.append('V+jets')
                colorsBkg.append('aquamarine')
            elif name == 'ttbar':
                labelsBkg.append(r'$t\bar{t}$')
                colorsBkg.append('r')

    # QCD scaling to data
    hData = histosData[0]
    hQCD = histosBkg[0]
    scale = np.sum(hData)/np.sum(hQCD)
    histosBkg[0] = histosBkg[0] * scale

    # convert data to scatter
    scatterData = (edgesData[0][:-1] + edgesData[0][1:])/2
    errorsData = np.sqrt(histosData[0])

    # calculate ratio and errors
    hTotalBkg = np.sum(histosBkg, axis=0)
    errorsTotalBkg = np.sqrt(hTotalBkg)

    for i, val in enumerate(hTotalBkg):
        if (val == 0): hTotalBkg[i] = 0.01
    
    hRatio = np.divide(histosData[0], hTotalBkg)
    errorsRatio = []
    for i in range(len(hRatio)):
        f2 = hRatio[i] * hRatio[i]
        a2 = errorsData[i] * errorsData[i] / (histosData[0][i] * histosData[0][i])
        b2 = errorsTotalBkg[i] * errorsTotalBkg[i] / (hTotalBkg[i] * hTotalBkg[i])
        sigma2 = f2 * (a2+b2)
        sigma = np.sqrt(sigma2)
        errorsRatio.append(sigma)
    errorsRatio = np.asarray(errorsRatio)

    plt.style.use([hep.style.CMS])
    f, axs = plt.subplots(2, 1, sharex=True, sharey=False, gridspec_kw={'height_ratios':[4,1],'hspace':0.05})
    axs = axs.flatten()
    plt.sca(axs[0])
    hep.histplot(histosBkg, edgesBkg[0], stack=False, ax=axs[0], label=labelsBkg, histtype='fill', facecolor=colorsBkg, edgecolor='black')
    plt.errorbar(scatterData, histosData[0], yerr=errorsData, fmt='o', color='k', label=labelsData[0])
    axs[0].set_yscale('log')
    axs[0].legend()
    axs[1].set_xlabel(xtitle)
    axs[0].set_ylabel(ytitle)
    plt.ylabel(ytitle, horizontalalignment='right', y=1.0)
    axs[1].set_ylabel("Data/MC")
    yMax = axs[0].get_ylim()
    axs[0].set_ylim([0.01, yMax[1]*100])
    hep.cms.text("Preliminary", loc=1)
    plt.legend(loc='best')

    plt.sca(axs[1])
    axs[1].axhline(y=1.0, xmin=0, xmax=1, color='r')
    axs[1].set_ylim([0.,2.1])
    plt.xlabel(xtitle, horizontalalignment='right', x=1.0)
    plt.errorbar(scatterData, hRatio, yerr=errorsRatio, fmt='o', color='k')

    plt.savefig('{}_{}.png'.format(var,year))
    plt.clf()
    '''
    plt.style.use([hep.style.CMS])
    ax = plt.subplot(1,1,1)
    #ax = ax.flatten()
    plt.sca(ax)
    hep.histplot(histosBkg,edgesBkg[0],stack=False,ax=ax,label=labelsBkg,histtype='fill',facecolor=colorsBkg,edgecolor='black')
    plt.errorbar(scatterData,histosData[0],yerr=errorsData,fmt='o',color='k',label=labelsData[0])
    ax.set_yscale('log')
    ax.legend()
    #plt.legend(loc=(0.05,0.4),ncol=2)
    plt.legend(loc='best')
    yMax = ax.get_ylim()
    print(yMax)
    plt.ylim([0.01, yMax[1]*100])
    plt.savefig('{}_{}.png'.format(var,year))
    plt.clf()
    '''

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year to process')
    args = parser.parse_args()

    for var, titles in varnames.items():
        plot(var, args.era, titles[0], titles[1])
