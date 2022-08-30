'''
   provide control distributions of jet quantities (pt, eta, phi) for each year for data and   bkg
   plotting in ROOT is a nightmare with python, so just use plotKinDist.py to plot them (python3)
'''
import ROOT, collections,sys,os
sys.path.append('./')
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd
from TIMBER.Tools.Plot import *
import helpers


ROOT.gROOT.SetBatch(True)
from THClass import THClass

# variables to plot (keys = columns in DF, vals = latex names)
varnames = {
    'pt0': 'Leading AK8 jet p_{T}',
    'pt1': 'Sublead AK8 jet p_{T}',
    'HT': 'Sum of lead and sublead jet p_{T}',
    'eta0': 'Leading AK8 jet #eta',
    'eta1': 'Sublead AK8 jet #eta',
    'phi0': 'Leading AK8 jet #varphi',
    'phi1': 'Sublead AK8 jet #varphi'   
}

#varnames={'phi0':'Leading AK8 jet #varphi'}

# main function to be called for processing
def select(setname, args):
    '''
	setname (str) = as appearing in dijet_nano/
	year    (str) = 16, 16APV, 17, 18
    '''
    year = args.era
    ROOT.ROOT.EnableImplicitMT(args.threads)
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(setname,year),year,1,1)
    selection.OpenForSelection('None')	# apply corrections, define a few columns, etc (does NOT make cuts)
    selection.ApplyTrigs(args.trigEff)

    # kinematic definitions
    selection.a.Define('pt0','Dijet_pt_corr[0]')
    selection.a.Define('pt1','Dijet_pt_corr[1]')
    selection.a.Define('HT','pt0+pt1')
    selection.a.Define('eta0','Dijet_eta[0]')
    selection.a.Define('eta1','Dijet_eta[1]')
    selection.a.Define('phi0','Dijet_phi[0]')
    selection.a.Define('phi1','Dijet_phi[1]')

    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    # book a group to save histos
    out = HistGroup('{}_{}'.format(setname,year))
    for varname in varnames.keys():
	histname = '{}_{}_{}'.format(setname, year, varname)
 	if ('pt' in varname):
	    hist_tuple = (varname,varname,100,350,2350)
	if (varname == 'HT'):
		hist_tuple = (varname,varname,200,350,4350)
	if 'eta' in varname:
	    hist_tuple = (varname,varname,48,-2.4,2.4)
	if 'phi' in varname:
	    hist_tuple = (varname,varname,64,-3.14,3.14)
	# Project dataframe into a histogram (hist name/binning tuple, variable to plot from dataframe, weight)
	hist = selection.a.GetActiveNode().DataFrame.Histo1D(hist_tuple,varname,'weight__nominal')
	#hist = selection.a.GetActiveNode().DataFrame.Histo1D(hist_tuple,varname)
	hist.GetValue()	# This gets the actual TH1 instead of a pointer to the TH1
	out.Add(varname,hist)

    return out

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-y', type=str, dest='era',
			action='store', required=True,
			help='Year to process')
    parser.add_argument('-t', type=int, dest='threads',
			action='store', required=False,
			default=2, help='Number of threads to use. On LPC, keep default at 2')
    '''
    parser.add_argument('--recreate', action='store_true',
			help='Whether to recreate the output rootfiles containing histograms. If False (not passed as flag), will attempt to recycle previously created histograms. If True (passed as flag), will create/recreate the histograms')
    parser.add_argument('--scale', action='store_true',
			help='Whether or not to scale data + background to unity. Default False.')
    '''

    args = parser.parse_args()
    
    #if args.recreate: args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')

    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')

    histgroups = {}
    # ZJetsHT400 is empty
    for setname in ['Data', 'WJetsHT400', 'WJetsHT600', 'WJetsHT800', 'ZJetsHT600', 'ZJetsHT800', 'ttbar-allhad', 'ttbar-semilep', 'QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000']:
	histgroup = select(setname, args)
	outfile = ROOT.TFile.Open('rootfiles/kinDist_{}_{}.root'.format(setname,args.era),'RECREATE')
	outfile.cd()
	histgroup.Do('Write')
	outfile.Close()
	del histgroup

    # now hadd all the relevant ones
    ExecuteCmd('hadd -f rootfiles/kinDist_QCD.root rootfiles/kinDist_QCDHT*_{}.root'.format(args.era))
    ExecuteCmd('hadd -f rootfiles/kinDist_VJets.root rootfiles/kinDist_*JetsHT*_{}.root'.format(args.era))
    ExecuteCmd('hadd -f rootfiles/kinDist_WJets.root rootfiles/kinDist_WJetsHT*_{}.root'.format(args.era))
    ExecuteCmd('hadd -f rootfiles/kinDist_ZJets.root rootfiles/kinDist_ZJetsHT*_{}.root'.format(args.era))
    ExecuteCmd('hadd -f rootfiles/kinDist_ttbar.root rootfiles/kinDist_ttbar-*_{}.root'.format(args.era))


    '''
    for setname in ['Data', 'WJetsHT400', 'WJetsHT600', 'WJetsHT800', 'ZJetsHT600', 'ZJetsHT800', 'ttbar-allhad', 'ttbar-semilep', 'QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000']:
	print('Preparing plots for {} {}'.format(setname, args.era))
	
	# perform histogram + ROOT file creation if flag is passed
	if args.recreate:
	    histgroup = select(setname, args)
	    outfile = ROOT.TFile.Open('rootfiles/kinDist_{}_{}.root'.format(setname,args.era),'RECREATE')
	    outfile.cd()
	    histgroup.Do('Write') # This will call TH1.Write() for all of the histograms in the group
	    outfile.Close()
	    del histgroup	# Now that they are saved out, drop from memory

	# Open histogram files that we saved
	infile = ROOT.TFile.Open('rootfiles/kinDist_{}_{}.root'.format(setname,args.era))
        # ... raise exception if we forgot to run with --recreate
        if infile == None:
            raise TypeError("rootfiles/kinDist_{}_{}.root does not exist, rerun with --recreate".format(setname,args.era))
	# Put histograms back into HistGroups
	histgroups[setname] = HistGroup(setname)
	for key in infile.GetListOfKeys(): # loop over histograms in the file
	    varname = key.GetName()
	    inhist = infile.Get(varname) # get it from the file
	    inhist.SetDirectory(0)
	    histgroups[setname].Add(varname,inhist)	# just add keyname not varname
	    print('Adding plot of variable {} for {}'.format(varname, setname))

    # for each variable to plot:
    for varname in varnames.keys():
	plot_filename = 'plots/{}_{}{}.%s'.format(varname,args.era,'_scaled' if args.scale else '')

	# get the background hists
	bkg_hists = OrderedDict()
	#for bkg in ['WJetsHT400', 'WJetsHT600', 'WJetsHT800', 'ZJetsHT600', 'ZJetsHT800', 'ttbar-allhad', 'ttbar-semilep', 'QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000']:
	for bkg in histgroups.keys():
	    histgroups[bkg][varname].SetTitle('%s 20%s'%(varname, args.era)) # empty title
	    # add all subgroups together, i.e. QCD = QCDHT700 + QCDHT1000 + QCDHT1500 + QCDHT2000
	    # to do so, first create the ordereddict of bkg histos. If the histo exists clone it, if not then add it to the dict
	    if 'QCD' in bkg:
		if 'QCD' not in bkg_hists.keys():
		    bkg_hists['QCD'] = histgroups[bkg][varname].Clone('QCD_'+varname)
		else:
		    bkg_hists['QCD'].Add(histgroups[bkg][varname])
	    elif 'WJets' in bkg:
		if 'WJets' not in bkg_hists.keys():
		    bkg_hists['WJets'] = histgroups[bkg][varname].Clone('WJets_'+varname)
	        else:
		    bkg_hists['WJets'].Add(histgroups[bkg][varname])
	    elif 'ZJets' in bkg:
                if 'ZJets' not in bkg_hists.keys():
                    bkg_hists['ZJets'] = histgroups[bkg][varname].Clone('ZJets_'+varname)
                else:
                    bkg_hists['ZJets'].Add(histgroups[bkg][varname])
	    elif 'ttbar' in bkg:
                if 'ttbar' not in bkg_hists.keys():
                    bkg_hists['ttbar'] = histgroups[bkg][varname].Clone('ttbar_'+varname)
                else:
                    bkg_hists['ttbar'].Add(histgroups[bkg][varname])

	# get background and data histos in the format required for EasyPlots()
	data = [histgroups['Data'].__getitem__(varname)]	# this list will have one item, the histogram for the given variable
	bkgs = [[]]	# this list contains one list, which contains all bkg histos
	for bkg in ['QCD','WJets','ttbar','ZJets']:	# plotting function stacks them in order, so put these in order largest -> smallest yield
	    bkgs[0].append(bkg_hists[bkg])

	# QCD scaling to data for each variable
	dataSum = data[0].Integral()
	qcdSum = bkgs[0][0].Integral()
	qcdScale = dataSum/qcdSum
	print('QCD scale: {}'.format(qcdScale))
	bkgs[0][0].Scale(qcdScale)

        # Use TIMBER EasyPlots() utility (Thank you Lucas!!!!)
	# https://github.com/lcorcodilos/TIMBER/blob/master/TIMBER/Tools/Plot.py#L376
	for extension in ['pdf','png']:
	    
	    EasyPlots(
		name = plot_filename%(extension),
		histlist = data,
		bkglist = bkgs,
		xtitle = varnames[varname]
	    )    
	    
	    CompareShapes(
		outfilename = plot_filename%(extension),
		year = args.era,
		prettyvarname = varnames[varname],
		#bkgs = OrderedDict([('QCD',bkgs[0][0]),('WJets',bkgs[0][1]),('ttbar',bkgs[0][2]),('ZJets',bkgs[0][3])]),
		bkgs = OrderedDict([('WJets',bkgs[0][1]),('ttbar',bkgs[0][2]),('ZJets',bkgs[0][3])]),
		signals = {'Data':data[0]},
		#colors={'WJets':3, 'ZJets':4, 'ttbar':2, 'QCD':5},
		colors={'WJets':3,'ZJets':4,'ttbar':2},
		scale=args.scale,
		logy=True
	    )
    '''
