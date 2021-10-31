import ROOT, glob
from TIMBER.Analyzer import TIMBERPATH, analyzer, Correction
from TIMBER.Tools.AutoPU import MakePU

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
    hptr = MakePU(a, '20%sUL'%args.era, fullname+'.root')
    hout = hptr.Clone()
    out.WriteTObject(hout, fullname)
    #h.Write()
    out.Close()
