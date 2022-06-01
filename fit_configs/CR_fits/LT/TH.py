from time import time
from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from TwoDAlphabet.helpers import make_env_tarball, cd, execute_cmd
from TwoDAlphabet.ftest import FstatCalc
import os
import numpy as np

def _get_other_region_names(pass_reg_name):
    return pass_reg_name, pass_reg_name.replace('loose','pass')

def _select_signal(row, args):
    signame = args[0]
    poly_order = args[1]
    if row.process_type == 'SIGNAL':
        if signame in row.process:
            return True
        else:
            return False
    elif 'Background' in row.process:
        if row.process == 'Background_'+poly_order:
            return True
        elif row.process == 'Background':
            return True
        else:
            return False
    else:
        return True
#------------------------------------------------------------------------------------------------------------
# NEED TO ADJUST THIS FUNCTION
#------------------------------------------------------------------------------------------------------------
def _load_CR_rpf(poly_order):
    twoD_CRonly = TwoDAlphabet('THfits_CR','TH.json', loadPrevious=True)
    params_to_set = twoD_CRonly.GetParamsOnMatch('rpf.*'+poly_order, 'MX_2000_MY_800_area', 'b')
    return {k:v['val'] for k,v in params_to_set.items()}
#------------------------------------------------------------------------------------------------------------

def _load_CR_rpf_as_SR(poly_order):
    params_to_set = {}
    for k,v in _load_CR_rpf(poly_order).items():
        params_to_set[k.replace('CR','SR')] = v
    return params_to_set

def _generate_constraints(nparams):
    out = {}
    for i in range(nparams):
        if i == 0:
            out[i] = {"MIN":0,"MAX":1}
        else:
            out[i] = {"MIN":-5,"MAX":5}
    return out

_rpf_options = {
    '0x0': {
        'form': '0.1*(@0)',
        'constraints': _generate_constraints(1)
    },
    '1x0': {
        'form': '0.1*(@0+@1*x)',
        'constraints': _generate_constraints(2)
    },
    '0x1': {
        'form': '0.1*(@0+@1*y)',
        'constraints': _generate_constraints(2)
    },
    '1x1': {
        'form': '0.1*(@0+@1*x)*(1+@2*y)',
        'constraints': _generate_constraints(3)
    },
    '1x2': {
        'form': '0.1*(@0+@1*x)*(1+@2*y+@3*y*y)',
        'constraints': _generate_constraints(4)
    },
    '2x1': {
        'form': '0.1*(@0+@1*x+@2*x**2)*(1+@3*y)',
        'constraints': _generate_constraints(4)
    },
    '2x2': {
        'form': '0.1*(@0+@1*x+@2*x**2)*(1+@3*y+@4*y**2)',
        'constraints': _generate_constraints(5)
    },
    '2x3': {
        'form': '0.1*(@0+@1*x+@2*x*x)*(1+@3*y+@4*y*y+@5*y*y*y)',
        'constraints': _generate_constraints(6)
    },
    '3x2': {
        'form': '0.1*(@0+@1*x+@2*x*x+@3*x*x*x)*(1+@4*y+@5*y*y)',
        'constraints': _generate_constraints(6)
    }
}

def test_make(SRorCR):
    '''
    Makes the workspace for ALL signals (all are included in the JSON config file)
    '''
    # for now (t\phi) the SR is entirely blinded and we are doing fits in the CR only.
    assert SRorCR == 'CR'  

    fr = {}
    # by default config file looks for CR, so change if necessary (not relevant now, keep anyway)
    if SRorCR == 'SR':
        fr['CR_pass'] = 'SR_pass'
        fr['CR_loose'] = 'SR_loose'

    twoD = TwoDAlphabet('THfits_{}'.format(SRorCR), 'TH.json', findreplace=fr, loadPrevious=False)
    qcd_hists = twoD.InitQCDHists()

    # this loop only runs once, since the only regions are CR_loose, CR_pass
    print('loose in r')
    print([_get_other_region_names(r) for r in twoD.ledger.GetRegions() if 'loose' in r])
    print('pass in r')
    print([_get_other_region_names(r) for r in twoD.ledger.GetRegions() if 'pass' in r])
    for l,p in [_get_other_region_names(r) for r in twoD.ledger.GetRegions() if 'loose' in r]:
        binning_l, _ = twoD.GetBinningFor(l)
	loose_name = 'Background_'+l
	qcd_l = BinnedDistribution(
		loose_name, qcd_hists[l],
		binning_l, constant=False
	)
	twoD.AddAlphaObj('Background',l,qcd_l)

	for opt_name, opt in _rpf_options.items():
	    qcd_rpfT = ParametricFunction(
		loose_name.replace('loose','rpfT')+'_'+opt_name,
		binning_l, opt['form'],
		constraints=opt['constraints']
	    )
	    qcd_p = qcd_l.Multiply(loose_name.replace('loose','pass')+'_'+opt_name, qcd_rpfT)
	    twoD.AddAlphaObj('Background_'+opt_name,p,qcd_p,title='Background')

    twoD.Save()

def test_fit(SRorCR, signal, tf, extra=''):
    '''
        SRorCR = 'CR', 'SR'	(for now, only looking at CR)
        signal [str] = 'MTOP-MHIGGS'
                MTOP : 800-1800 GeV, 100 GeV intervals
                MHIGGS : 75, 100, 125, 175, 200, 250, 350, 450, 500 GeV
        tf [str] = 0x0, 0x1, 1x0, 1x1, 1x2, 2x2
    '''
    assert SRorCR == 'CR'
    working_area = 'THfits_{}'.format(SRorCR)

    # might have to change this to the line below (uncommented) but I think this first line should work.
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    #twoD = TwoDAlphabet(working_area, 'TH.json', loadPrevious=True)

    # create ledger, make an area for it with card
    subset = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), tf)
    twoD.MakeCard(subset, 'TprimeB-{}-{}_area'.format(signal, tf))
    # perform fit
    twoD.MLfit('TprimeB-{}-{}_area'.format(signal,tf),rMin=-1,rMax=20,verbosity=1,extra=extra)

def test_plot(SRorCR, signal, tf):
    working_area = 'THfits_{}'.format(SRorCR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    #twoD = TwoDAlphabet(working_area, 'TH.json', loadPrevious=True)

    subset = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), tf)
    twoD.StdPlots('TprimeB-{}-{}_area'.format(signal,tf), subset)

def _gof_for_FTest(twoD, subtag, card_or_w='card.txt'):

    run_dir = twoD.tag+'/'+subtag
    
    with cd(run_dir):
        gof_data_cmd = [
            'combine -M GoodnessOfFit',
            '-d '+card_or_w,
            '--algo=saturated',
            '-n _gof_data'
        ]

        gof_data_cmd = ' '.join(gof_data_cmd)
        execute_cmd(gof_data_cmd)

def test_FTest(poly1, poly2, SRorCR='CR', signal='TprimeB-1800-125'):
    '''
    Perform an F-test using existing working areas
    '''
    assert SRorCR == 'CR'
    working_area = 'THfits_{}'.format(SRorCR)
    
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    binning = twoD.binnings['default']
    nBins = (len(binning.xbinList)-1)*(len(binning.ybinList)-1)
    
    # Get number of RPF params and run GoF for poly1
    params1 = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), poly1).alphaParams
    rpfSet1 = params1[params1["name"].str.contains("rpf")]
    nRpfs1  = len(rpfSet1.index)
    _gof_for_FTest(twoD, 'TprimeB-1800-125-{}_area'.format(poly1), card_or_w='card.txt')
    gofFile1 = working_area+'/TprimeB-1800-125-{}_area/higgsCombine_gof_data.GoodnessOfFit.mH120.root'.format(poly1)

    # Get number of RPF params and run GoF for poly2
    params2 = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), poly2).alphaParams
    rpfSet2 = params2[params2["name"].str.contains("rpf")]
    nRpfs2  = len(rpfSet2.index)
    _gof_for_FTest(twoD, 'TprimeB-1800-125-{}_area'.format(poly2), card_or_w='card.txt')
    gofFile2 = working_area+'/TprimeB-1800-125-{}_area/higgsCombine_gof_data.GoodnessOfFit.mH120.root'.format(poly2)

    base_fstat = FstatCalc(gofFile1,gofFile2,nRpfs1,nRpfs2,nBins)
    print(base_fstat)

    def plot_FTest(base_fstat,nRpfs1,nRpfs2,nBins):
        from ROOT import TF1, TH1F, TLegend, TPaveText, TLatex, TArrow, TCanvas, kBlue, gStyle
        gStyle.SetOptStat(0000)

        if len(base_fstat) == 0: base_fstat = [0.0]

        ftest_p1    = min(nRpfs1,nRpfs2)
        ftest_p2    = max(nRpfs1,nRpfs2)
        ftest_nbins = nBins
        fdist       = TF1("fDist", "[0]*TMath::FDist(x, [1], [2])", 0,max(10,1.3*base_fstat[0]))
        fdist.SetParameter(0,1)
        fdist.SetParameter(1,ftest_p2-ftest_p1)
        fdist.SetParameter(2,ftest_nbins-ftest_p2)

        pval = fdist.Integral(0.0,base_fstat[0])
        print 'P-value: %s'%pval

        c = TCanvas('c','c',800,600)    
        c.SetLeftMargin(0.12) 
        c.SetBottomMargin(0.12)
        c.SetRightMargin(0.1)
        c.SetTopMargin(0.1)
        ftestHist_nbins = 30
        ftestHist = TH1F("Fhist","",ftestHist_nbins,0,max(10,1.3*base_fstat[0]))
        ftestHist.GetXaxis().SetTitle("F = #frac{-2log(#lambda_{1}/#lambda_{2})/(p_{2}-p_{1})}{-2log#lambda_{2}/(n-p_{2})}")
        ftestHist.GetXaxis().SetTitleSize(0.025)
        ftestHist.GetXaxis().SetTitleOffset(2)
        ftestHist.GetYaxis().SetTitleOffset(0.85)
        
        ftestHist.Draw("pez")
        ftestobs  = TArrow(base_fstat[0],0.25,base_fstat[0],0)
        ftestobs.SetLineColor(kBlue+1)
        ftestobs.SetLineWidth(2)
        fdist.Draw('same')

        ftestobs.Draw()
        tLeg = TLegend(0.6,0.73,0.89,0.89)
        tLeg.SetLineWidth(0)
        tLeg.SetFillStyle(0)
        tLeg.SetTextFont(42)
        tLeg.SetTextSize(0.03)
        tLeg.AddEntry(ftestobs,"observed = %.3f"%base_fstat[0],"l")
        tLeg.AddEntry(fdist,"F-dist, ndf = (%.0f, %.0f) "%(fdist.GetParameter(1),fdist.GetParameter(2)),"l")
        tLeg.Draw("same")

        model_info = TPaveText(0.2,0.6,0.4,0.8,"brNDC")
        model_info.AddText('p1 = '+poly1)
        model_info.AddText('p2 = '+poly2)
        model_info.AddText("p-value = %.2f"%(1-pval))
        model_info.Draw('same')
        
        latex = TLatex()
        latex.SetTextAlign(11)
        latex.SetTextSize(0.06)
        latex.SetTextFont(62)
        latex.SetNDC()
        latex.DrawLatex(0.12,0.91,"CMS")
        latex.SetTextSize(0.05)
        latex.SetTextFont(52)
        latex.DrawLatex(0.65,0.91,"Preliminary")
        latex.SetTextFont(42)
        latex.SetTextFont(52)
        latex.SetTextSize(0.045)
        c.SaveAs(working_area+'/ftest_{0}_vs_{1}_notoys.png'.format(poly1,poly2))

    plot_FTest(base_fstat,nRpfs1,nRpfs2,nBins)

def test_GoF(SRorCR, signal, tf, condor=False):
    assert SRorCR == 'CR'
    working_area = 'THfits_{}'.format(SRorCR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    signame = 'TprimeB-'+signal
    if not os.path.exists(twoD.tag+'/'+signame+'-{}_area/card.txt'.format(tf)):
        print('{}/{}-area/card.txt does not exist, making card'.format(twoD.tag,signame))
        subset = twoD.ledger.select(_select_signal, signame, tf)
        twoD.MakeCard(subset, signame+'_area')
    if condor == False:
        twoD.GoodnessOfFit(
            signame+'-{}_area'.format(tf), ntoys=500, freezeSignal=0,
            condor=False
        )
    else:
        twoD.GoodnessOfFit(
            signame+'-{}_area'.format(tf), ntoys=500, freezeSignal=0,
            condor=True, njobs=10
        )

def test_GoF_plot(SRorCR, signal, tf):
    '''Plot the GoF in THfits_<SRorCR>/TprimeB-<signal>_area (condor=True indicates that condor jobs need to be unpacked)'''
    assert SRorCR == 'CR'
    signame = 'TprimeB-'+signal
    plot.plot_gof('THfits_'+SRorCR,'{}-{}_area'.format(signame,tf), condor=False)

if __name__ == "__main__":
    # create workspace with ALL signals
    #test_make('CR')

    #test_fit('CR', '1800-125', '0x0', '--robustHesse 1')
    #test_plot('CR', '1800-125', '0x0')

    #test_fit('CR', '1800-125', '0x1', '--robustHesse 1')
    #test_plot('CR', '1800-125', '0x1')

    #test_fit('CR', '1800-125', '1x0', '--robustHesse 1')
    #test_plot('CR', '1800-125', '1x0')

    #test_fit('CR', '1800-125', '1x1', '--robustHesse 1')
    #test_plot('CR', '1800-125', '1x1')

    #test_fit('CR', '1800-125', '2x1', '--robustHesse 1')
    #test_plot('CR', '1800-125', '2x1')

    #test_fit('CR', '1800-125', '1x2', '--robustHesse 1')
    #test_plot('CR', '1800-125', '1x2')

    #test_fit('CR', '1800-125', '2x2', '--robustHesse 1')
    #test_plot('CR', '1800-125', '2x2')

    #test_fit('CR', '1800-125', '2x3', '--robustHesse 1')
    #test_plot('CR', '1800-125', '2x3')

    #test_fit('CR', '1800-125', '3x2', '--robustHesse 1')
    #test_plot('CR', '1800-125', '3x2')

    '''
    test_FTest("0x0","0x1")
    test_FTest("0x0","1x0")
    test_FTest("0x1","1x1")
    test_FTest("1x0","1x1")
    test_FTest("1x1","1x2")
    test_FTest("1x1","2x1")
    test_FTest("1x2","2x2")
    test_FTest("2x1","2x2")
    test_FTest("2x2","3x2")
    test_FTest("2x2","2x3")
    '''

    #test_GoF('CR','1800-125','2x1')
    test_GoF_plot('CR','1800-125','2x1')