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
	    print(row.process, poly_order)
            return True
        elif row.process == 'Background':
            print(row.process, poly_order)
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
            out[i] = {"MIN":-500,"MAX":500}
        else:
            out[i] = {"MIN":-500,"MAX":500}
    return out

_rpf_options = {
    '0x0': {
        'form': '(@0)',
        'constraints': _generate_constraints(1)
    },
    '1x0': {
        'form': '(@0+@1*x)',
        'constraints': _generate_constraints(2)
    },
    '0x1': {
        'form': '(@0+@1*y)',
        'constraints': _generate_constraints(2)
    },
    '1x1': {
        'form': '(@0+@1*x)*(@2+@3*y)',
        'constraints': _generate_constraints(4)
    },
    '2x1': {
	'form': '(@0+@1*x+@2*x**2)*(@3+@4*y)',
	'constraints': _generate_constraints(5)
    },
    '2x2': {
        'form': '(@0+@1*x+@2*x**2)*(@3+@4*y*@5*y**2)',
        'constraints': _generate_constraints(6)
    },
    '3x2': {
        'form': '(@0+@1*x+@2*x**2+@3*x**3)*(@4+@5*y)',
        'constraints': _generate_constraints(6)
    }
}

def test_make(SRorCR='',fr={}):
    twoD = TwoDAlphabet('THfits_{}'.format(SRorCR),'TH.json',loadPrevious=False,findreplace=fr)
    qcd_hists = twoD.InitQCDHists()

    # this loop only runs once, since the only regions are CR_loose, CR_pass
    for l,p in [_get_other_region_names(r) for r in twoD.ledger.GetRegions() if 'loose' in r]:
        binning_l, _ = twoD.GetBinningFor(l)
    loose_name = 'Background_'+l
    qcd_l = BinnedDistribution(
		loose_name, qcd_hists[l],
		binning_l, constant=False
	)
    twoD.AddAlphaObj('Background',l,qcd_l,title='Multijet')

    for opt_name, opt in _rpf_options.items():
	qcd_rpf = ParametricFunction(
                loose_name.replace('loose','rpf')+'_'+opt_name,
                binning_l, opt['form'],
                constraints=opt['constraints']
        )
        qcd_p = qcd_l.Multiply(loose_name.replace('loose','pass')+'_'+opt_name,qcd_rpf)
        twoD.AddAlphaObj('Background'+'_'+opt_name,p,qcd_p,title='Multijet')

    twoD.Save()

def test_fit(SRorCR='', signal='', tf='', defMinStrat=0, extra='--robustHesse 1'):
    working_area = 'THfits_{}'.format(SRorCR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)

    subset = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), tf)
    twoD.MakeCard(subset, 'TprimeB-{}-{}_area'.format(signal, tf))

    twoD.MLfit('TprimeB-{}-{}_area'.format(signal,tf),rMin=-1,rMax=3,verbosity=2,defMinStrat=defMinStrat,extra=extra)

def test_plot(SRorCR='', signal='', tf='', prefit=False):
    working_area = 'THfits_{}'.format(SRorCR)
    twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)
    subset = twoD.ledger.select(_select_signal, 'TprimeB-{}'.format(signal), tf)
    twoD.StdPlots('TprimeB-{}-{}_area'.format(signal,tf), subset, prefit=prefit)

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
    #assert SRorCR == 'CR'
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

def test_GoF(SRorCR, signal, tf='', condor=True):
    #assert SRorCR == 'CR'
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
            condor=True, njobs=50
        )

def test_GoF_plot(SRorCR, signal, tf='', condor=True):
    '''Plot the GoF in ttbar<SRorCR>/TprimeB-<signal>_area (condor=True indicates that condor jobs need to be unpacked)'''
    signame = 'TprimeB-'+signal
    plot.plot_gof('THfits_'+SRorCR,'{}-{}_area'.format(signame,tf), condor=condor)

def load_RPF(twoD,signal='1800-125',tf='2x1'):
    params_to_set = twoD.GetParamsOnMatch('rpf.*', 'TprimeB-{}-{}_area'.format(signal,tf), 'b')
    return {k:v['val'] for k,v in params_to_set.items()}

def test_SigInj(SRorCR, r, signal='1800-125', tf='2x1', condor=False):
    '''Perform a signal injection test'''
    twoD = TwoDAlphabet('THfits_{}'.format(SRorCR), 'THfits_{}/runConfig.json'.format(SRorCR), loadPrevious=True)
    params = load_RPF(twoD, signal, tf)
    twoD.SignalInjection(
        'TprimeB-{}-{}_area'.format(signal,tf),
        injectAmount = r,       # amount of signal to inject (r=0 <- bias test)
	card_or_w = 'initialFitWorkspace.root',
        ntoys = 500,
	njobs = 50,
        blindData = False,      # working with toy data, no need to blind
        setParams = params,     # give the toys the same RPF params
        verbosity = 0,
        extra = '' if int(r) == 0 else '--expectSignal={}'.format(r),
        condor = condor)

def test_SigInj_plot(SRorCR, r, signal='1800-125',tf='2x1', condor=False):
    plot.plot_signalInjection('THfits_{}'.format(SRorCR),'TprimeB-{}-{}_area'.format(signal,tf), injectedAmount=r, condor=condor)

def test_Impacts(SRorCR,signal='1800-125',tf='2x1'):
    twoD = TwoDAlphabet('THfits_{}'.format(SRorCR), 'THfits_{}/runConfig.json'.format(SRorCR), loadPrevious=True)
    twoD.Impacts('TprimeB-{}-{}_area'.format(signal,tf), cardOrW='initialFitWorkspace.root', extra='-t 20')

if __name__ == "__main__":
    for toy in [2]:
	findreplace = {'TH_toys/PseudoDataToy_CDF_method_seed1_unblindedFail.root':'TH_toys/PseudoDataToy_CDF_method_seed{}_unblindedFail.root'.format(toy)}

	for mass in [1800]: #[1000, 2400, 3000]:
	    tag = 'SR_toy%s_%s-125'%(toy,mass)
	    signal = '%s-125'%mass
	    tf = '2x1'
	    findreplace["TprimeB-1800-125"] = "TprimeB-%s-125"%mass

	    #test_make(SRorCR=tag, fr=findreplace)
	    #for tf in _rpf_options.keys():
		#print('--------------------------- %s ------------------------'%tf)
		#test_fit(SRorCR=tag, signal=signal, tf=tf, defMinStrat=1, extra='--robustFit 1')
		#test_plot(SRorCR=tag, signal=signal, tf=tf)
		#test_GoF(SRorCR=tag, signal=signal, tf=tf, condor=True)
		#test_GoF_plot(SRorCR=tag, signal=signal, tf=tf, condor=True)


	    test_fit(SRorCR=tag, signal=signal, tf=tf, defMinStrat=1, extra='--robustFit 1')
	    #test_plot(SRorCR=tag, signal=signal, tf=tf)
	    #for r in [0.0, 0.15, 0.5, 1.0, 3.0, 5.0]:
		#test_SigInj(SRorCR=tag, r=r, signal=signal, tf=tf, condor=True)
		#test_SigInj_plot(SRorCR=tag, r=r, signal=signal,tf=tf, condor=True)

	    #test_GoF(SRorCR=tag, signal=signal, tf=tf, condor=True)
	    #test_GoF_plot(SRorCR=tag, signal=signal, tf=tf, condor=True)

	    '''
            test_FTest(poly1='0x1', poly2='1x1', SRorCR=tag, signal=signal)
            test_FTest(poly1='1x0', poly2='1x1', SRorCR=tag, signal=signal)
            test_FTest(poly1='0x0', poly2='1x1', SRorCR=tag, signal=signal)
            test_FTest(poly1='1x1', poly2='2x1', SRorCR=tag, signal=signal)
            test_FTest(poly1='1x1', poly2='2x2', SRorCR=tag, signal=signal)
            test_FTest(poly1='1x1', poly2='3x2', SRorCR=tag, signal=signal)
            test_FTest(poly1='2x1', poly2='2x2', SRorCR=tag, signal=signal)
            test_FTest(poly1='2x1', poly2='3x2', SRorCR=tag, signal=signal)
            test_FTest(poly1='2x2', poly2='3x2', SRorCR=tag, signal=signal)
	    '''
