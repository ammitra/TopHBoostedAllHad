from TwoDAlphabet.twoDalphabet import TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
import ROOT
from collections import OrderedDict

def _generate_constraints(nparams):
    out = {}
    for i in range(nparams):
        if i == 0:
            out[i] = {"MIN":0,"MAX":1}
        else:
            out[i] = {"MIN":-5,"MAX":5}
    return out

def _get_other_region_names(pass_reg_name):
    return pass_reg_name, pass_reg_name.replace('fail','loose'),pass_reg_name.replace('fail','pass')
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

def _getParams(line):
    '''
    helper function for makeRPF(), acts on each line of the rpf_params .txt 
    file to get the final parameters. This way, whole file isn't saved in memory.
    param format:
            Background_CR_rpfT_par0: 0.999999999868 +/- 0.148048177441
    '''
    # get param name (everything before colon)
    name =  line.split(':')[0]
    # get actual param value
    param = line.split(':')[1].split('+/-')[0].strip()

    return (name, float(param))

def makeRPF(fitDir, paramFile, poly):
    '''
    fitDir [str] = '/path/to/2DAlphabet/workspace/dir/'
    paramFile [str] = '/path/to/rpf_params_fitb.txt'
    poly [str] = RPF polynomial order, e.g. '2x2'

    * NOTE * assumes that the 2DAlphabet fit has already been performed 
    and the workspace exists.

    Gets the binning from the 2DAlphabet-generated workspace and the 
    RPF parameters from the 2DAlphabet-generated .txt file, then 
    constructs the ParametricFunction associated with those parameters.
    '''
    twoD = TwoDAlphabet(fitDir, fitDir+'/runConfig.json', loadPrevious=True)
    # for now we'll just hard-code this. We're looking in the CR, so we'll get the binning from 'CR_fail' region
    for f,l,p in [_get_other_region_names(r) for r in twoD.ledger.GetRegions() if 'fail' in r]:
        print('regions detected in workspace: {}, {}, {}\n'.format(f,l,p))
        binning_f, _ = twoD.GetBinningFor(f)
    fail_name = 'Background_{}'.format(f)

    # hard-code the region detection as well. L = 'rpfL', T = 'rpfT'
    rpfName = 'rpfL' if 'rpfL' in paramFile else 'rpfT'
    
    # construct the actual ParametricFunction
    rpf_func = ParametricFunction(
        fail_name.replace('fail',rpfName),
        binning_f, _rpf_options[poly]['form'],
        constraints=_rpf_options[poly]['constraints']
    )

    # get rpf params from the .txt file
    params = OrderedDict()
    with open(paramFile) as f:
        for line in f:
            # output of _getParams() is a tuple (paramName, paramVal)
            paramName, paramVal = _getParams(line)
            params[paramName] = paramVal
    
    # quick check to ensure that the number of params matches the polynomial order
    nParams = _rpf_options[poly]['form'].count('@')
    assert(len(params.keys()) == nParams)

    # status update
    print('{} polynomial : {}\n'.format(rpfName, _rpf_options[poly]['form']))
    # update user and set parameter values in the rpf_func ParametricFunction object
    count = 0
    for iparam, param_val in params.items():
        print('Parameter @{} = {} = {}'.format(count, iparam, param_val))
        rpf_func.setFuncParam(iparam, param_val)
        count += 1

    # save the histogram in a root file
    rpfFile = ROOT.TFile.Open('{}.root'.format(rpfName), 'RECREATE')
    rpfFile.cd()

    # create and fill RPF shape histogram
    out_hist = rpf_func.binning.CreateHist(rpfName,cat='')
    for ix in range(1, out_hist.GetNbinsX()):
        for iy in range(1, out_hist.GetNbinsY()):
            out_hist.SetBinContent(ix, iy, rpf_func.getBinVal(ix, iy))

    out_hist.SetDirectory(0)
    out_hist.Write()
    rpfFile.Close()

'''
fitDir = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR'
rpfL = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfL_fitb.txt'
rpfT = '/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_10_6_14/src/TH/FLT/THfits_CR/TprimeB-1800-125-_area/rpf_params_Background_CR_rpfT_fitb.txt'
makeRPF(fitDir,rpfT,'2x1')
makeRPF(fitDir,rpfL,'1x0')
'''