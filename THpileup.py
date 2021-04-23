import ROOT, glob
from TIMBER.Analyzer import TIMBERPATH, analyzer, Correction

def MakePU(a, name, era):
    '''Automatically perform the standard pileup calculation on the analyzer object.

    @param a (analyzer): Object to manipulate and return.
    @param era (str): 2016(UL), 2017(UL), 2018(UL)

    Returns:
        analyzer: Manipulated input.
    '''
    ftemplate = ROOT.TFile.Open(TIMBERPATH+'/TIMBER/data/Pileup/pileup_%s.root'%era)
    htemplate = ftemplate.Get('pileup')
    binning = (name,name, htemplate.GetNbinsX(), htemplate.GetXaxis().GetXmin(), htemplate.GetXaxis().GetXmax())
    autoPU = a.DataFrame.Histo1D(binning,"Pileup_nTrueInt")
    # print ('AutoPU: Extracting Pileup_nTrueInt distribution')
    ftemplate.Close()
    return autoPU

def ApplyPU(a,name,era):
    c_PU = Correction('pileup','TIMBER/Framework/include/Pileup_weight.h',
                      ['THpileup.root', 'pileup_%s'%era,
                       name, 'pileup'],
                       corrtype="weight")
    a.AddCorrection(c_PU)
    return a

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    args = parser.parse_args()

    fullname = '%s_%s'%(args.setname,args.era)
    out = ROOT.TFile.Open('THpileup_%s.root'%(fullname),'RECREATE')
    a = analyzer('raw_nano/%s.txt'%(fullname))
    h = MakePU(a, fullname, '20%sUL'%args.era)
    out.cd()
    h.Write()
    out.Close()