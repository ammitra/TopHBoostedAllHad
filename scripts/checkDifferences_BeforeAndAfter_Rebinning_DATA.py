'''
check differences b/w old binning and new binning for ttbar
'''
import ROOT

new_bin_dir = '/store/user/ammitra/topHBoostedAllHad/selection/'
old_bin_dir = '/store/user/ammitra/topHBoostedAllHad/selection_backup_GOOD_butOnly60-260GeV_binning_in_mPhi/'

fname_base = 'THselection_HT750_{}.root'

redirector = 'root://cmseos.fnal.gov/'

histname = 'MthvMh_particleNet_SR_loose__nominal'

for year in ['DataA_18','DataB_16APV','DataB_17','DataB_18','DataC_16APV','DataC_17','DataC_18','DataD_16APV','DataD_17','DataE_16APV','DataE_17','DataF_16','DataF_16APV','DataF_17','DataG_16','DataH_16','DataWithB_17','Data_16','Data_16APV','Data_17','Data_18','Data_Run2']:
    if year == 'DataB_17': continue
    fOld = ROOT.TFile.Open('%s%s%s'%(redirector,old_bin_dir,fname_base.format(year)),'READ')
    fNew = ROOT.TFile.Open('%s%s%s'%(redirector,new_bin_dir,fname_base.format(year)),'READ')

    hOld = fOld.Get(histname)
    hNew = fNew.Get(histname)

    print('ttbar {}'.format(year))
    print('old: {}'.format(hOld.Integral()))
    print('new: {}'.format(hNew.Integral()))
    print('\n')

    fOld.Close()
    fNew.Close()

# no major difference in integrals observed before and after rebinning
