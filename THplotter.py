from argparse import Namespace
from glob import glob
from THselection import THselection
from THstudies import THstudies
from TIMBER.Tools.Common import DictStructureCopy, CompileCpp, ExecuteCmd, OpenJSON, StitchQCD
from TIMBER.Tools.Plot import CompareShapes
from TIMBER.Analyzer import Correction
import multiprocessing, ROOT

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

def CombineCommonSets(groupname,doStudies=False):
    '''Which stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep)

    @param groupname (str, optional): "QCD" or "ttbar".
    '''
    if groupname not in ["QCD","ttbar"]:
        raise ValueError('Can only combine QCD or ttbar')
    config = OpenJSON('THconfig.json')
    for y in ['16','17','18']:
        baseStr = 'rootfiles/TH%s_{0}_{1}{2}.root'%('studies' if doStudies else 'selection')
        if groupname == 'ttbar':
            for v in ['']:
                if v == '':
                    ExecuteCmd('hadd -f %s %s %s'%(
                        baseStr.format('ttbar',y,''),
                        baseStr.format('ttbar-allhad',y,''),
                        baseStr.format('ttbar-semilep',y,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f %s %s %s'%(
                            baseStr.format('ttbar',y,v3),
                            baseStr.format('ttbar-allhad',y,v3),
                            baseStr.format('ttbar-semilep',y,v3))
                        )
        elif groupname == 'QCD':
            ExecuteCmd('hadd -f %s %s %s %s %s'%(
                baseStr.format('QCD',y,''),
                baseStr.format('QCDHT700',y,''),
                baseStr.format('QCDHT1000',y,''),
                baseStr.format('QCDHT1500',y,''),
                baseStr.format('QCDHT2000',y,''))
            )

    MakeRun2(groupname)    

def MakeRun2(setname,doStudies=False):
    t = 'studies' if doStudies else 'selection'
    ExecuteCmd('hadd -f rootfiles/TH{1}_{0}_Run2.root rootfiles/TH{1}_{0}_16.root rootfiles/TH{1}_{0}_17.root rootfiles/TH{1}_{0}_18.root'.format(setname,t))

def multicore(doStudies=False):
    CompileCpp('THmodules.cc')
    files = GetAllFiles()

    teff = {
        "16": Correction("TriggerEff16",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_16.root','Pretag'], corrtype='weight'),
        "17": Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17.root','Pretag'], corrtype='weight'),
        "18": Correction("TriggerEff18",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_18.root','Pretag'], corrtype='weight')
    }

    pool = multiprocessing.Pool(processes=1 if doStudies else 8,maxtasksperchild=1)
    nthreads = 8 if doStudies else 2
    process_args = []
    for f in files:
        setname, era = GetProcYearFromTxt(f)
        
        if doStudies:
            if 'Data' not in setname:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era]))
        else:
            if 'Data' not in setname and 'QCD' not in setname:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era]))
                if not doStudies:
                    for jme in ['JES','JER','JMS','JMR']:
                        for v in ['up','down']:
                            process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='%s_%s'%(jme,v),trigEff=teff[era]))
            else:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era]))

    if doStudies:
        pool.map(THstudies,process_args)
    else:
        pool.map(THselection,process_args)

def plot(histname,fancyname):
    files = [f for f in glob('rootfiles/THstudies_*_Run2.root') if (('_QCD_' in f) or ('_ttbar_' in f) or ('_TprimeB-1200' in f))]
    hists = GetHistDict(histname,files)

    CompareShapes('plots/%s_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kYellow,'ttbar':ROOT.kRed,'TprimeB-1200':ROOT.kBlack},
                   scale=False, stackBkg=True, 
                   doSoverB=True)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--recycle', dest='recycle',
                        action='store_true', default=False,
                        help='Recycle existing files and just plot.')
    parser.add_argument('--studies', dest='studies',
                        action='store_true', default=False,
                        help='Run the studies instead of the selections.')

    args = parser.parse_args()
    if not args.recycle:
        multicore(args.studies)
        CombineCommonSets('QCD',args.studies)
        CombineCommonSets('ttbar',args.studies)
        
        if args.studies:
            MakeRun2('QCD',args.studies)
            MakeRun2('ttbar',args.studies)
            for m in range(800,1900,100):
                MakeRun2('TprimeB-%s'%m,args.studies)
        else:
            MakeRun2('Data',args.studies)

    if args.studies:
        histNames = {
            'pt0':'Lead jet p_{T} (GeV)',
            'pt1':'Sublead jet p_{T} (GeV)',
            'HT':'Scalar sum dijet p_{T} (GeV)',
            'deltaEta': '|#Delta #eta|',
            'deltaY': '|#Delta y|',
            'deltaPhi': '|#Delta #phi|',
            'mt_deepTag': 'Top jet mass (with DeepAK8 tag)',
            'mt_particleNet': 'Top jet mass (with ParticleNet tag)',
            'mH_deepTagMD': 'Higgs jet mass (with DeepAK8 tag)',
            'mH_particleNetMD': 'Higgs jet mass (with ParticleNet tag)',
            't_deepTagMD':'DeepAK8 top tag score',
            'H_deepTagMD':'DeepAK8 Higgs tag score',
            't_particleNet':'ParticleNet top tag score',
            'H_particleNet':'ParticleNet Higgs tag score',
        }
        tempFile = ROOT.TFile.Open('rootfiles/THstudies_TprimeB-1300_18.root','READ')
        allValidationHists = [k.GetName() for k in tempFile.GetListOfKeys() if 'Idx' not in k.GetName()]
        for h in allValidationHists:
            print ('Plotting: %s'%h)
            if h in histNames.keys():
                plot(h,histNames[h])
            else:
                plot(h,h)
