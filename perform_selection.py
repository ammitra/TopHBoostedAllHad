from argparse import Namespace
from glob import glob
from THselection import THselection
from THstudies import THstudies
from TIMBER.Tools.Common import DictStructureCopy, CompileCpp, ExecuteCmd, OpenJSON, StitchQCD
from TIMBER.Tools.Plot import CompareShapes
from TIMBER.Analyzer import Correction
import multiprocessing, ROOT, time

def GetAllFiles():
    return [f for f in glob('dijet_nano/*_snapshot.txt') if f != '']
def GetProcYearFromTxt(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    return pieces[0], pieces[1]
def GetProcYearFromROOT(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    return pieces[1], pieces[2]

def GetHistDict(histname, all_files):
    all_hists = {
        'bkg':{},'sig':{},'data':None
    }
    for f in all_files:
        proc, year = GetProcYearFromROOT(f)
        tfile = ROOT.TFile.Open(f)
        hist = tfile.Get(histname)
        if hist == None:
            raise ValueError('Histogram %s does not exist in %s.'%(histname,f))
        hist.SetDirectory(0)
        if 'Tprime' in proc:
            all_hists['sig'][proc] = hist
        elif proc == 'Data':
            all_hists['data'] = hist
        else:
            all_hists['bkg'][proc] = hist
    return all_hists

def CombineCommonSets(groupname,doStudies=False,modstr=''):
    '''Which stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep)
    @param groupname (str, optional): "QCD" or "ttbar".
    '''
    if groupname not in ["QCD","ttbar"]:
        raise ValueError('Can only combine QCD or ttbar')
    config = OpenJSON('THconfig.json')
    for y in ['16','17','18']:
        baseStr = 'rootfiles/TH%s_{0}{2}_{1}{3}.root'%('studies' if doStudies else 'selection')
        if groupname == 'ttbar':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f %s %s %s'%(
                        baseStr.format('ttbar',y,modstr,''),
                        baseStr.format('ttbar-allhad',y,modstr,''),
                        baseStr.format('ttbar-semilep',y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f %s %s %s'%(
                            baseStr.format('ttbar',y,modstr,v3),
                            baseStr.format('ttbar-allhad',y,modstr,v3),
                            baseStr.format('ttbar-semilep',y,modstr,v3))
                        )
        elif groupname == 'QCD':
            ExecuteCmd('hadd -f %s %s %s %s %s'%(
                baseStr.format('QCD',y,modstr,''),
                baseStr.format('QCDHT700',y,modstr,''),
                baseStr.format('QCDHT1000',y,modstr,''),
                baseStr.format('QCDHT1500',y,modstr,''),
                baseStr.format('QCDHT2000',y,modstr,''))
            )


def MakeRun2(setname,doStudies=False,modstr=''):
    t = 'studies' if doStudies else 'selection'
    ExecuteCmd('hadd -f rootfiles/TH{1}_{0}{2}_Run2.root rootfiles/TH{1}_{0}{2}_16.root rootfiles/TH{1}_{0}{2}_17.root rootfiles/TH{1}_{0}{2}_18.root'.format(setname,t,modstr))

if __name__ == "__main__":
    CompileCpp('THmodules.cc')
    files = GetAllFiles()

    teff = {
        "16": Correction("TriggerEff16",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_16.root','Pretag'], corrtype='weight'),
        "17": Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17.root','Pretag'], corrtype='weight'),
        "18": Correction("TriggerEff18",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_18.root','Pretag'], corrtype='weight')
    }

    '''
    process_args = []
    for f in files:
	setname, era = GetProcYearFromTxt(f)
	
	if 'Data' not in setname and 'QCD' not in setname:
	    process_args.append(Namespace(threads=1,setname=setname, era=era, variation='None', trigEff=teff[era],topcut=''))
	    for jme in ['JES','JER','JMS','JMR']:
		for v in ['up','down']:
                    process_args.append(Namespace(threads=1,setname=setname,era=era,variation='%s_%s'%(jme,v),trigEff=teff[era],topcut=''))
	else:
	    process_args.append(Namespace(threads=1,setname=setname,era=era,variation='None',trigEff=teff[era],topcut=''))
    '''

    process_args = {}
    for f in files:
	setname, era = GetProcYearFromTxt(f)
	if 'Data' not in setname and 'QCD' not in setname:
	    process_args['{} {} None'.format(setname, era)] = Namespace(threads=1,setname=setname, era=era, variation='None', trigEff=teff[era],topcut='')
	    for jme in ['JES','JER','JMS','JMR']:
                for v in ['up','down']:
		    process_args['{} {} {}_{}'.format(setname,era,jme,v)] = Namespace(threads=1,setname=setname,era=era,variation='%s_%s'%(jme,v),trigEff=teff[era],topcut='')
	else:
	    process_args['{} {} None'.format(setname, era)] = Namespace(threads=1,setname=setname,era=era,variation='None',trigEff=teff[era],topcut='')


    # Due to (seemingly) random segfaults when running this, we have to check whether or not the given setname/era/variation combo has already been performed
    SF = glob('rootfiles/*.root')       # will have format THselection_<setname>_<era>_<var>_<up/down>.root
    combinations = []
    for f in SF:
        name = f.split('.')[0].split('/')[1]
        name = name.split('_')
        setname = name[1]
        era = name[2]
	#print('{} {}'.format(setname, era))
        if len(name) == 3:      # we're dealing with something without variations
            var = 'None'
	else:
	    var = '{}_{}'.format(name[3],name[4])
	combinations.append('{} {} {}'.format(setname,era,var))	        

    for process, args in process_args.items():
	#print(process)
        if process in combinations:
	    print('---- {} ALREADY PERFORMED ----'.format(process))
	else:
	    start = time.time()
	    print('PROCESSING: {} {} {}'.format(args.setname, args.era, args.variation))
	    THselection(args)
	    print('Total time: %s'%(time.time()-start))

    # housekeeping 
    CombineCommonSets('QCD',False)
    CombineCommonSets('ttbar',False)
    MakeRun2('Data',False)
