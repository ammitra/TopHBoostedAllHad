void makeHisto(const char* fName) {
	TFile f(fName, "UPDATE");
	// make T score histogram
	f.Get("Events")->Draw("Dijet_particleNet_TvsQCD>>TScore(200,0.,1.)");
	f.Get("TScore")->Write();
	// make MD_H score histogram
	f.Get("Events")->Draw("Dijet_particleNetMD_Xbb/(Dijet_particleNetMD_Xbb+Dijet_particleNetMD_QCD)>>HScore(200,0.,1.)");
	f.Get("HScore")->Write();
	f.Close();
}
