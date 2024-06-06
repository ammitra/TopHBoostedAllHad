from TIMBER.Tools.Plot import CompareShapes, EasyPlots
from collections import OrderedDict
import ROOT

f = ROOT.TFile.Open('TEST_NMERGED.root','READ')
'''
for region in ['SR_loose','SR_pass','ttbarCR_fail','ttbarCR_pass']:
    print('Plotting top/phi in %s'%region)
    hTop = f.Get('nmerged_top_%s'%region)
    hPhi = f.Get('nmerged_phi_%s'%region)
    prettyvarname = 'N_{subjets}'
    signals = {'top':hTop,'phi':hPhi}
    names = {'top':'top-candidate','phi':'#phi-candidate'}
    colors = {'top':ROOT.kRed,'phi':ROOT.kBlue}
    outname = 'plots/top_vs_phi_merged_%s.jpg'%region
    if region == 'SR_loose':
	regionName = 'SR Loose'
    elif region == 'SR_pass':
	regionName = 'SR Pass'
    elif region == 'ttbarCR_fail':
	regionName = 't#bar{t} CR Fail'
    else:
	regionName = 't#bar{t} CR Pass'
    CompareShapes(
	outname,
	1,
	prettyvarname,
	bkgs={},
	signals=signals,
	names=names,
	colors=colors,
	histtitle='Number of subjets within R = 0.8 of jet, %s'%regionName,
	scale=True
    )
'''
'''
for jet in ['top','phi']:
    hSRP = f.Get('nmerged_%s_SR_pass'%jet)
    hTTP = f.Get('nmerged_%s_ttbarCR_pass'%jet)
    print('plotting %s jet in SR pass and TTCR pass'%jet)
    prettyvarname = 'N_{subjets}'
    signals = {'SRP':hSRP,'TTCRP':hTTP}
    names = {'SRP':'SR Pass','TTCRP':'t#bar{t} CR'}
    colors = {'SRP':ROOT.kRed,'TTCRP':ROOT.kBlue}
    outname = 'plots/merged_%s_ttCR_vs_SR.jpg'%jet
    if jet == 'top':
	jetname = 'Top'
    else:
	jetname = '#phi'
    CompareShapes(
        outname,
        1,
        prettyvarname,
        bkgs={},
        signals=signals,
        names=names,
        colors=colors,
        histtitle='Number of subjets within R = 0.8 of %s-candidate jet'%jetname,
        scale=True
    )
'''
for region in ['ttbarCR_pass']:
    # Check the splitting b/w the top and phi candidate in ttCRP
    hTop = f.Get('split_top_%s'%(region))
    hPhi = f.Get('split_phi_%s'%(region))
    prettvarname = 'Top match category'
    signals = {'top':hTop,'phi':hPhi}
    names = {'top':ROOT.kRed,'phi':ROOT.kBlue}
    colors = {'top':ROOT.kRed,'phi':ROOT.kBlue}
    outname = 'plots/top_vs_phi_splitting_%s.jpg'%region
    regionName = 't#bar{t} CR Pass'
    CompareShapes(
        outname,
        1,
        prettyvarname,
        bkgs={},
        signals=signals,
        names=names,
        colors=colors,
        histtitle='Number of subjets within R = 0.8 of jet, %s'%regionName,
	axislabels='',
        scale=True
    )
