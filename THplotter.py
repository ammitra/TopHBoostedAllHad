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

def multicore(infiles=[],doStudies=False,topcut=''):
    CompileCpp('THmodules.cc')
    if infiles == []: files = GetAllFiles()
    else: files = infiles

    teff = {
        "16": Correction("TriggerEff16",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_16.root','Pretag'], corrtype='weight'),
        "17": Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17.root','Pretag'], corrtype='weight'),
        "18": Correction("TriggerEff18",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_18.root','Pretag'], corrtype='weight')
    }

    pool = multiprocessing.Pool(processes=4 if doStudies else 6,maxtasksperchild=1)
    nthreads = 4 if doStudies else 2
    process_args = []
    for f in files:
        setname, era = GetProcYearFromTxt(f)
        
        if doStudies:
            if 'Data' not in setname:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era],topcut=topcut))
        else:
            if 'Data' not in setname and 'QCD' not in setname:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era],topcut=topcut))
                if not doStudies:
                    for jme in ['JES','JER','JMS','JMR']:
                        for v in ['up','down']:
                            process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='%s_%s'%(jme,v),trigEff=teff[era],topcut=topcut))
            else:
                process_args.append(Namespace(threads=nthreads,setname=setname,era=era,variation='None',trigEff=teff[era],topcut=topcut))

    start = time.time()
    if doStudies:
        pool.map(THstudies,process_args)
    else:
        for a in process_args:
            print ('PROCESSING: %s %s %s'%(a.setname, a.era, a.variation))
            THselection(a)
        # pool.map(THselection,process_args)

    print ('Total multicore time: %s'%(time.time()-start))

def plot(histname,fancyname,era='Run2'):
    files = [f for f in glob('rootfiles/THstudies_*_%s.root'%era) if (('_QCD_' in f) or ('_ttbar_' in f) or ('_TprimeB-1000' in f))]
    hists = GetHistDict(histname,files)

    if histname.startswith('deep') or histname.startswith('particleNet'):
        optimize = True
    else:
        optimize = False
    CompareShapes('plots/%s_%s.pdf'%(histname,era),1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kOrange,'ttbar':ROOT.kRed,'TprimeB-1000':ROOT.kBlack},
                   scale=True, stackBkg=True, 
                   doSoverB=optimize,forceBackward=True if 'deepTag_H' in histname else False,
                   logy=True)

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
        multicore(doStudies=args.studies)
    
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
                plot(h,histNames[h],'16')
                plot(h,histNames[h],'17')
                plot(h,histNames[h],'18')
            else:
                plot(h,h)
                plot(h,h,'16')
                plot(h,h,'17')
                plot(h,h,'18')
