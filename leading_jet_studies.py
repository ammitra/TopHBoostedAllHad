import ROOT, time, glob
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd
from TIMBER.Tools.Plot import CompareShapes, EasyPlots
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def leadMass(args):
    print('PROCESSING: {} {}'.format(args.setname, args.era))
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    # base setup
    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname, args.era),int(args.era),1,1)
    selection.OpenForSelection('None')
    selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt_corr, Dijet_eta, Dijet_phi, Dijet_msoftdrop_corrT)')
    selection.a.Define('mth','hardware::InvariantMass(Dijet_vect)')
    selection.a.Define('m_avg','(Dijet_msoftdrop_corrT[0]+Dijet_msoftdrop_corrT[1])/2')
    selection.ApplyTrigs(args.trigEff)
    # come back to this node for each of the three plots of interest
    baseNode = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    out = ROOT.TFile.Open('rootfiles/leadMassStudies_{}_{}.root'.format(args.setname,args.era),'RECREATE')
    out.cd()

    # now we are interested in the leading jet mass after:
    #	1) immediately after preselection (snapshot)
    massPlots = HistGroup('massPlots')
    selection.a.Define('m0_nominal','Dijet_msoftdrop_corrT[0]')	    # leading jet mass after snapshot phase (nominal)
    massPlots.Add('m0_nominal',selection.a.DataFrame.Histo1D(('m0_nominal','Lead jet mass after snapshot',50,0,250),'m0_nominal','weight__nominal'))

    for t in ['deepTag','particleNet']:
        top_tagger = '%s_TvsQCD'%t
	
	#   2) immediately after applying the standard top tag cut
	print('----- m0_tight : {} -----'.format(top_tagger))
	selection.a.SetActiveNode(baseNode)
	selection.ApplyTopPick(tagger=top_tagger,invert=False)
	selection.a.Define('m0_tight','Top_msoftdrop_corrT')
	massPlots.Add('m0_tight',selection.a.DataFrame.Histo1D(('m0_tight','Lead jet mass after top pick',50,0,250),'m0_tight','weight__nominal'))

        #   3) immediately after applying the loose (but not tight) top tag cut
	print('----- m0_loose : {} -----'.format(top_tagger))
	selection.a.SetActiveNode(baseNode)
	selection.ApplyTopPick(tagger=top_tagger,invert=True)
	selection.a.Define('m0_loose','Top_msoftdrop_corrT')
	massPlots.Add('m0_loose',selection.a.DataFrame.Histo1D(('m0_loose','Lead jet mass after loose cut',50,0,250),'m0_loose','weight__nominal'))

    massPlots.Do('Write')
    out.Close()
    print('Processing time: {} sec'.format(time.time()-start))

def GetAllFiles():
    return [f for f in glob.glob('dijet_nano/*_snapshot.txt') if f != '']

def GetProcYearFromTxt(filename):
    '''
    format:	dijet_nano/setname_era_snapshot.txt
    '''
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    proc = pieces[0]
    year = pieces[1]
    return proc, year

def GetProcYearFromROOT(filename):
    '''
    format:	rootfiles/leadMassStudies_setname_era.root
    '''
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    proc = pieces[1]
    year = pieces[2]
    return proc, year

def GetHistDict(histname, all_files):
    all_hists = {'bkg':{}, 'sig':{}, 'data':None}
    for f in all_files:
	proc, year = GetProcYearFromROOT(f)
	tfile = ROOT.TFile.Open(f)
	hist = tfile.Get(histname)
        if hist == None:
            raise ValueError('Histogram %s does not exist in %s.'%(histname,f))
        hist.SetDirectory(0)
        if 'MX' in proc:
            all_hists['sig'][proc] = hist
        elif proc == 'Data':
            all_hists['data'] = hist
        else:
            all_hists['bkg'][proc] = hist
    return all_hists

def CombineCommonSets(groupname):
    '''
    First stitch together QCD or ttbar (ttbar-allhad+ttbar-semilep):
        leadMassStudies_QCD_{year}.root
        leadMassStudies_ttbar_{year}.root
    Then uses MakeRun2() to combine all years. Final output:  
        leadMassStudies_QCD_Run2.root
        leadMassStudies_ttbar_Run2.root
    '''
    for y in ['16','17','18']:
	baseStr = 'rootfiles/leadMassStudies_{0}_{1}.root'
	if groupname == 'ttbar':
	    ExecuteCmd('hadd -f %s %s %s'%(
		baseStr.format('ttbar',y),
		baseStr.format('ttbar-allhad',y),
		baseStr.format('ttbar-semilep',y))
	    )
	elif groupname == 'QCD':
	    ExecuteCmd('hadd -f %s %s %s %s %s'%(
		baseStr.format('QCD',y),
		baseStr.format('QCDHT700',y),
		baseStr.format('QCDHT1000',y),
		baseStr.format('QCDHT1500',y),
		baseStr.format('QCDHT2000',y))
	    )

if __name__ == "__main__":
    from argparse import Namespace, ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    args = parser.parse_args()
    args.threads = 1
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')
    CompileCpp('THmodules.cc')
    leadMass(args)

    '''
    # produce the trigger effs for all years beforehand, pass them to Namespace after
    teff16 = Correction("TriggerEff"+'16','TIMBER/Framework/include/EffLoader.h',['THtrigger2D_16.root','Pretag'], corrtype='weight')
    teff17 = Correction("TriggerEff"+'17','TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17.root','Pretag'], corrtype='weight')
    teff18 = Correction("TriggerEff"+'18','TIMBER/Framework/include/EffLoader.h',['THtrigger2D_18.root','Pretag'], corrtype='weight')

    # cross check against existing files
    existing = glob.glob('rootfiles/leadMassStudies*.root')

    # generate arguments 
    process_args = []
    for f in GetAllFiles():
	proc, year = GetProcYearFromTxt(f)
	# check to see if it's been done
	for g in existing:
	    p,y = GetProcYearFromROOT(g)
	    #print('{} - {}, {} - {}'.format(proc,p,year,y))
	    if (p == proc) and (y == year):
		print('------ {} {} already performed, skipping ------'.format(proc,year))
	    else:
		if year == '16':
	    	    process_args.append(Namespace(threads=1,setname=proc,era=year,trigEff=teff16))
		elif year == '17':
	    	    process_args.append(Namespace(threads=1,setname=proc,era=year,trigEff=teff17))
        	elif year == '18':
	    	    process_args.append(Namespace(threads=1,setname=proc,era=year,trigEff=teff18))

    CompileCpp('THmodules.cc')
    for args in process_args:
	leadMass(args)
    '''
