'''script to plot the kinematics of the top and phi candidate jets in the ttbarCR and SR'''
import ROOT

def plot(year):
    for proc in ['ttbar']: # 'TprimeB-1800-125'
	f = ROOT.TFile.Open('rootfiles/compare_kinematics_ttCR_SR_%s_%s.root'%(proc,year),'READ')
        for jet in ['Top','Higgs']:
            for var in ['pt','eta','phi','msoftdrop_corr{}'.format('T' if jet=='Top' else 'H')]:
                print('Plotting {} for {} jet'.format(var,jet))
                h_cr = f.Get('{}_{}_ttbarCR_pass__nominal'.format(jet,var))
                h_sr = f.Get('{}_{}_SR_pass__nominal'.format(jet,var))

		jetname = jet if jet == 'Top' else '#phi'

		if var == 'pt':
		    xtitle = '%s candidate p_{T}'%jetname
		    ytitle = 'Events/20 GeV'
		elif var == 'eta':
		    xtitle = '%s candidate #eta'%jetname
		    ytitle = 'Events/10'
		elif var == 'phi':
                    xtitle = '%s candidate #varphi'%jetname
                    ytitle = 'Events/10'
		else:
                    xtitle = '%s candidate m_{SD}'%jetname
                    ytitle = 'Events/5 GeV'

		ytitle = 'A.U.'

		h_cr.SetTitle('%s candidate %s ttbarCR vs SR'%(jetname,var))
		h_cr.SetXTitle(xtitle)
		h_cr.SetYTitle(ytitle)

		h_cr.Scale(1./h_cr.Integral())
		h_sr.Scale(1./h_sr.Integral())
		h_sr.SetLineColor(ROOT.kRed)

		c = ROOT.TCanvas('c','c')
		c.cd()
		rp = ROOT.TRatioPlot(h_cr,h_sr,"diff")
                rp.Draw()
		if var == 'pt':
		    rp.GetUpperRefXaxis().SetRangeUser(0.,1250.)
		    rp.GetLowerRefXaxis().SetRangeUser(0.,1250.)
		rp.GetLowYaxis().SetNdivisions(505)
		rp.GetUpperPad().cd()
		leg = ROOT.TLegend(0.6,0.7,0.8,0.85)
		leg.AddEntry(h_cr,"t#bar{t} CR","l")
		leg.AddEntry(h_sr,"SR","le")
		leg.Draw()
		c.Update()
		c.Draw()
		c.Print("plots/ttCR_vs_SR_kinematics_{}_{}_{}.png".format(jet,var,year))

for year in ['Run2']:#['16','16APV','17','18','Run2']:
    plot(year)
