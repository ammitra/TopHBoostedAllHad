'''
check differences b/w old binning and new binning for ttbar
'''
import ROOT

new_bin_dir = '/store/user/ammitra/topHBoostedAllHad/selection/'
old_bin_dir = '/store/user/ammitra/topHBoostedAllHad/selection_backup_GOOD_butOnly60-260GeV_binning_in_mPhi/'

fname_base = 'THselection_HT750_ZJets_{}.root'

redirector = 'root://cmseos.fnal.gov/'

histname = 'MthvMh_particleNet_SR_loose__nominal'

for year in ['16','16APV','17','18']:
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
