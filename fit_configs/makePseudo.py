from logging import root
import re
import ROOT
import sys
import os
import random
from TwoDAlphabet.twoDalphabet import TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from makeRPF import makeRPF
from collections import OrderedDict

# for constructing data-like toys in the SR from the RPF shapes generated in the CR FLT fit

# global variables needed for makeRPF()
'''
fitDir = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR'
rpfL = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfL_fitb.txt'
rpfT = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfT_fitb.txt'
makeRPF(fitDir,rpfT,'2x1')
makeRPF(fitDir,rpfL,'1x0')
'''

def getYear(inFile):
    '''
    not really needed here, since we're not scaling bkgs by year
    '''
    if ('16' or 'APV' in inFile):
        return '2016'
    elif ('17' in inFile):
        return '2017'
    elif ('18' in inFile):
        return '2018'
    else:
        print('Year not recognized for {}'.format(inFile))
        sys.exit()

def constructTT(inFiles, region, SRorCR='CR'):
    '''
    inFiles = [
        "THselection_ttbar_16.root",
        "THselection_ttbar_16APV.root",
        "THselection_ttbar_17.root",
        "THselection_ttbar_18.root"
    ]

    region [str] = "fail", "loose", "pass"
    '''
    assert(SRorCR=='CR')
    tagger = 'particleNet'

    ttbar = None
    for inFile in inFiles:
        year = getYear(inFile)
        f = ROOT.TFile.Open(inFile)

        # get the nominal ttbar histo and store it temporarily
        ttbar_temp = f.Get("MthvMh_{}_{}_{}__nominal".format(tagger,SRorCR,region))
        # populate ttbar file on the first go
        if not ttbar:
            ttbar = ttbar_temp.Clone('ttbar_{}'.format(region))
            ttbar.Reset()
            ttbar.SetDirectory(0)

        ttbar.Add("ttbar_temp")
        f.Close()

    return ttbar


def subtractBkg():
    '''
    takes data from SR fail and subtracts ttbar and V+Jets bkgs from it

    returns a TH2D of the data minus background (giving QCD est) in SR fail
    '''
    tagger = 'particleNet'
    region = 'SR_fail'
    rootfile_dir = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_11_1_4/src/PostAPV/TopHBoostedAllHad/rootfiles'
    dataFile = 'THselection_Data_Run2.root'
    
    print('Subtracting backgrounds from data in {}...'.format(region))

    # for this analysis we are considering ttbar (combined semilep+allhad) and V+jets
    # different analyses could modify this dict and the following loop logic
    bkg_SR_fail = {'ttbar':None, 'WJets':None, 'ZJets':None, 'Data_Run2':None}
    # loop through all backgrounds to be subtracted
    for bkg in bkg_SR_fail.keys():
        # loop through all years
        for year in ['16','16APV','17','18']:
            # get m_t vs m_phi(H) SR fail histogram (nominal) - same hist name for all files
            histName = 'MthvMh_{}_{}__nominal'.format(tagger,region)
            if ('Data' in bkg):
                # data has been added to this bkg dict, just for debug purposes later
                fileName = '{}/THselection_{}.root'.format(rootfile_dir,bkg)
                print('Opening Run2 Data file {}'.format(fileName))
                f = ROOT.TFile.Open(fileName)
                print('Acquiring histogram {}'.format(histName))
                bkg_temp = f.Get(histName)
                bkg_SR_fail[bkg] = bkg_temp.Clone('{}_{}_nominal'.format(bkg,region))
                bkg_SR_fail[bkg].Reset()
                bkg_SR_fail[bkg].SetDirectory(0)
                bkg_SR_fail[bkg].Add(bkg_temp)
                f.Close()
            else:
                # open the specific background file (nominal) for given year.
                # file will look like, e.g. ..../THselection_ttbar_16APV.root 
                fileName = '{}/THselection_{}_{}.root'.format(rootfile_dir,bkg,year)
                print('Opening {}'.format(fileName))
                f = ROOT.TFile.Open(fileName)
                print('Acquiring histogram {}'.format(histName))
                bkg_temp = f.Get(histName)
                # check if bkg histogram exists yet in our dict
                if not bkg_SR_fail[bkg]:
                    bkg_SR_fail[bkg] = bkg_temp.Clone('{}_{}_nominal'.format(bkg,region))
                    bkg_SR_fail[bkg].Reset()
                    bkg_SR_fail[bkg].SetDirectory(0)
                bkg_SR_fail[bkg].Add(bkg_temp)
                f.Close()

    # at this point the dict should contain the bkgs and data in SR_fail. Now just subtract
    dataMinusBkg = bkg_SR_fail['Data_Run2'].Clone('dataMinusBkg_{}_nominal'.format(region))
    print('Performing bkg subtraction from Run2 Data')
    for bkg, hist in bkg_SR_fail.items():
        if 'Data' in bkg:
            pass
        else:   # perform subtraction via Add() TH2D method
            print('Subtracting {} from Run2 data'.format(bkg))
            dataMinusBkg.Add(hist, -1.)
            # test bkgs subtracted individually, just for debug
            dataMinusIndividualBkg = bkg_SR_fail['Data_Run2'].Clone('dataMinus{}_only'.format(bkg))
            dataMinusIndividualBkg.Add(hist, -1.)
            bkg_SR_fail['DataMinus{}'.format(bkg)] = dataMinusIndividualBkg

    # add data minus bkgs hist to dict for debug
    bkg_SR_fail['Data_minus_background'] = dataMinusBkg

    # debug file to check that results make sense
    test = ROOT.TFile.Open('bkgs_SR_fail.root','RECREATE')
    test.cd()
    for hist in bkg_SR_fail.values():
        hist.SetDirectory(0)
        hist.Write()
    test.Close()
    
    # return TH2D corresponding to QCD estimate in SR fail
    return bkg_SR_fail['Data_minus_background']

def constructQCD():
    '''
    construct QCD estimate in SR loose and pass regions from data-bkg (QCD) in SR fail
    '''
    regions = {
        'Loose':{}, 
        'Tight':{}
        }

    # get ratios - can be changed for future analyses
    rpfL_name = 'rpfL'  # file name same as histo name, might not always be the case tho
    rpfL = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/{}.root'.format(rpfL_name)   # Loose-to-Fail ratio
    rpfT_name = 'rpfT'
    rpfT = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/rpfT.root'   # Tight-to-Loose ratio

    # construct
    




























def applyRatio(ratioHist, ratioFile):
    '''
    ratioHist [TH2D] = 2D ratio histogram
    ratioFile [str] = name of ratio file containing hist
    '''
    ratio = ratioHist.Clone(ratioHist.GetName())
    f = ROOT.TFile.Open(ratioFile)

    for i in range(1, ratio.GetNBinsX()+1):
        for j in range(1, ratio.GetNBinsY()+1):
            ratioVal = ratio.GetBinContent(i,j)
            xVal = "blah"