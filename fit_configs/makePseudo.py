import re
import ROOT
import sys
import os
import random
from makeRPF import makeRPF

# for constructing data-like toys in the SR from the RPF shapes generated in the CR FLT fit


# global variables needed for makeRPF()
fitDir = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR'
rpfL_params = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfL_fitb.txt'
rpfT_params = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfT_fitb.txt'

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

def Multiply(h1, h2, name=''):
    '''
    h1, h2 = TH2Ds with different binning (nBins_h1 > nBins_h2)
    namne [str] = name of output hist
    Loops over bins in h1, get the corresponding value at that coordinate in h2.
    Then, multiply the value at h2 coord by the bin value in h1
    returns TH2D corresponding to h1 * h2
    '''
    print('Multiplying {} x {}'.format(h1.GetName(),h2.GetName()))
    nh1 = (h1.GetNbinsX(),h1.GetNbinsY())
    nh2 = (h2.GetNbinsX(),h2.GetNbinsY())
    print('{} binning : {}\n{} binning : {}'.format(h1,nh1,h2,nh2))
    finalHist = h1.Clone(name)
    # loop over bins in h1
    for i in range(0, h1.GetNbinsX()+1):
        for j in range(0, h1.GetNbinsY()+1):
            h1Val = h1.GetBinContent(i,j)
            xVal = h1.GetXaxis().GetBinCenter(i)
            yVal = h1.GetYaxis().GetBinCenter(j)
            ih2 = h2.GetXaxis().FindBin(xVal)
            jh2 = h2.GetYaxis().FindBin(yVal)
            h2Val = h2.GetBinContent(ih2,jh2)
            finalHist.SetBinContent(i,j,h1Val*h2Val)
    finalHist.SetDirectory(0)
    return finalHist

def constructQCD():
    '''
    construct QCD estimate in SR loose and pass regions from data-bkg (QCD) in SR fail
    '''
    # first, generate R_LF and R_TL ratios and get histograms (will also store in root file)
    rpfL = makeRPF(fitDir,rpfL_params,'1x0')
    rpfT = makeRPF(fitDir,rpfT_params,'2x1')

    # next, perform background subtraction (will also generate data minus bkg root file)
    QCD_SR_Fail = subtractBkg()

    # book an output root file
    outFile = ROOT.TFile.Open('QCD_SR_distributions.root','RECREATE')
    outFile.cd()
    # get QCD distribution in SR Loose and Tight, write them to output root file
    qcdFail = QCD_SR_Fail.Clone('QCD_Fail')
    qcdFail.SetDirectory(0)
    qcdLoose = Multiply(qcdFail, rpfL, 'QCD_Loose')
    qcdLoose.SetDirectory(0)
    qcdL_tmp = qcdLoose.Clone('qcdL_temp')
    qcdTight = Multiply(qcdL_tmp, rpfT, 'QCD_Tight')
    qcdTight.SetDirectory(0)
    # close file
    outFile.Close()



    '''
    # get ratio info - can be changed for future analyses
    rpfL_name = 'rpfL'  # file name same as histo name, might not always be the case tho
    rpfL_file = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/{}.root'.format(rpfL_name)   # Loose-to-Fail ratio
    rpfT_name = 'rpfT'
    rpfT_file = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/{}.root'.format(rpfT_name)   # Tight-to-Loose ratio

    regions = {
	    'Fail':{'rName':'dataMinusBkg_SR_fail_nominal','rFile':'bkgs_SR_fail.root','rHist':None},
        'rpfL':{'rName':rpfL_name, 'rFile':rpfL_file, 'rHist':None},
        'rpfT':{'rName':rpfT_name, 'rFile':rpfT_file, 'rHist':None}
        }

    # get ratio shapes
    for region in regions.keys():
        print('Getting {} {}'.format(region, regions[region]['rName']))
        f = ROOT.TFile.Open(regions[region]['rFile'])
        regions[region]['rHist'] = f.Get(regions[region]['rName'])
        regions[region]['rHist'].SetDirectory(0)
        f.Close()

    # now, get QCD distribution in Loose region
    qcdFail = regions['Fail']['rHist'].Clone('QCD_Fail')  # clone QCD in SR_fail
    qcdLoose = Multiply(qcdFail, regions['rpfL']['rHist'], 'QCD_Loose') # multiply: loose = fail * rpfL
    qcdLoose.SetDirectory(0)
    regions.update({'Loose':{'rHist': qcdLoose}})

    # QCD distribution in Tight region = Loose * rpfT
    qcdL_temp = qcdLoose.Clone('qcd_loose_temp')
    qcdTight = Multiply(qcdL_temp, regions['rpfT']['rHist'], 'QCD_Tight')
    qcdTight.SetDirectory(0)
    regions.update({'Tight':{'rHist': qcdTight}})

    # now, add them all to ROOT file for debug
    outFile = ROOT.TFile.Open('QCD_SR_distributions.root','RECREATE')
    outFile.cd()
    for r in regions.keys():
        if 'rpf' not in r:
            regions[r]['rHist'].SetDirectory(0)
            regions[r]['rHist'].Write()
    outFile.Close()
    '''
    # return qcd estimate in all three regions, just in case you want to use this function later
    return (qcdFail, qcdLoose, qcdTight)

def getCumulativePDF(h2_pdf, h2_name):
    print('Creating cumulativeP PDF {}'.format(h2_name))
    nx = h2_pdf.GetNbinsX()
    ny = h2_pdf.GetNbinsY()
    hPDF = ROOT.TH1F(h2_name,"",nx*ny,0,nx*ny)
    cumulativeBin = 0
    for i in range(1,nx+1):
        for j in range(1,ny+1):
            cumulativeBin += 1
            pdf = h2_pdf.GetBinContent(i,j)+hPDF.GetBinContent(cumulativeBin-1)
            hPDF.SetBinContent(cumulativeBin,pdf)
    return hPDF

def generatePDF():
    '''
    generates a PDF from ttbar/V+Jet simulation and QCD from ratios
    returns: 2D PDF, its cumulative PDF and the nEvents from estimate
    '''
    return




constructQCD()