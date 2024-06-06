'''
Create the postfit projections in x and y of the Pass region, with appropriate CCLE formatting.
Will use for final plots in paper.
'''
from time import time
from TwoDAlphabet import plot
from TwoDAlphabet.twoDalphabet import MakeCard, TwoDAlphabet
from TwoDAlphabet.alphawrap import BinnedDistribution, ParametricFunction
from TwoDAlphabet.helpers import make_env_tarball, cd, execute_cmd
from TwoDAlphabet.ftest import FstatCalc
import os
import numpy as np
import pandas

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

working_area = 'THfits_SR'

twoD = TwoDAlphabet(working_area, '{}/runConfig.json'.format(working_area), loadPrevious=True)

subset = twoD.ledger.select(_select_signal, 'TprimeB-1800-125', '')

runDir = 'THfits_SR/TprimeB-1800-125-_area'

with cd(runDir):
    plotter = plot.Plotter(subset, twoD, 'b', loadExisting=False)
    pads = pandas.DataFrame()
    for region, group in plotter.df.groupby('region'):
	if 'pass' not in region:
	    continue
	print('region: {}'.format(region))
	binning,_ = plotter.twoD.GetBinningFor(region)
	for logyFlag in [False]:
	    ordered_bkgs = plotter._order_df_on_proc_list(
		group[group.process_type.eq('BKG')], proc_type='BKG',
		alphaBottom=(not logyFlag))
	signals = group[group.process_type.eq('SIGNAL')]

	for proj in ['postfit_projx','postfit_projy']:
	    if 'projy' in proj:
		print('\n\n-------------------------------TEST------------------------------\n\n')
		plotter.yaxis1D_title = 'Events / 100 GeV'
	    else:
		plotter.yaxis1D_title = 'Events / 15 GeV'
	    for islice in range(3):
		projn = proj+str(islice)
		sig_projn = projn
		sig_projn = projn.replace('postfit','prefit')
		this_data =      plotter.Get(row=group.loc[group.process_type.eq('DATA')].iloc[0], hist_type=projn)
		this_totalbkg =  plotter.Get(row=group.loc[group.process_type.eq('TOTAL')].iloc[0], hist_type=projn)
		these_bkgs =    [plotter.Get(row=ordered_bkgs.iloc[irow], hist_type=projn) for irow in range(ordered_bkgs.shape[0])]
		these_signals = [plotter.Get(row=signals.iloc[irow], hist_type=sig_projn) for irow in range(signals.shape[0])]


		plotter.slices['x'][region] = {'vals': binning.xSlices,'idxs':binning.xSliceIdx}
		plotter.slices['y'][region] = {'vals': binning.ySlices,'idxs':binning.ySliceIdx}

		print(plotter.slices)

		slice_edges = (
		    plotter.slices['x' if 'y' in proj else 'y'][region]['vals'][islice],
		    binning.xtitle if 'y' in proj else binning.ytitle,
		    plotter.slices['x' if 'y' in proj else 'y'][region]['vals'][islice+1],
		    'GeV'
		)

		slice_str = '%s < %s < %s %s'%slice_edges

		out_pad_name = '{d}/base_figs/{projn}_{reg}{logy}'.format(
		    d=plotter.dir, projn=projn, reg=region,
		    logy='' if logyFlag == False else '_logy')

		plot.make_pad_1D(out_pad_name, data=this_data, bkgs=these_bkgs, signals=these_signals,
		    subtitle=slice_str, totalBkg=this_totalbkg,
		    logyFlag=logyFlag, year=plotter.twoD.options.year,
		    extraText='Preliminary', savePDF=True, savePNG=True, ROOTout=False)
		pads = pads.append({'pad':out_pad_name+'.png', 'region':region, 'proj':projn, 'logy':logyFlag}, ignore_index=True)

    for logy in ['']:
	for proj in ['postfit_projx','postfit_projy']:
	    these_pads = pads.loc[pads.proj.str.contains(proj)]
	    print('call 1')
	    print(these_pads)
	   
	    print('these_pads.logy')
	    print(these_pads.logy)
 
	    if logy == '':
		these_pads = these_pads.loc[these_pads.logy.eq(False)]
		print('call 2')
		print(these_pads)
	    
	    else:
		these_pads = these_pads.loc[these_pads.logy.eq(True)]
	    print('call 3')
            print(these_pads)
	    
	    these_pads = these_pads.sort_values(by=['region','proj']).pad.to_list()
	    out_can_name = '{d}/{proj}{logy}'.format(d='.', proj=proj,logy=logy)
	    print('call 4')
	    print(these_pads)
	    plot.make_can(out_can_name, these_pads)
