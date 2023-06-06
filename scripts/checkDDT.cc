#include "ROOT/RVec.hxx"
#include "TFile.h"
#include "TIMBER/Framework/include/common.h"
#include <string>
#include <vector>
#include <random> // because TRandom wouldn't work in this case..

using namespace ROOT::VecOps;

RVec<float> DDT_discr(TFile* f, RVec<float> pt, RVec<float> msd) {
    TH2F* hist = (TH2F*)f->Get("SoftdropMass_particleNet_TvsQCD_mistagRate0p01_maxBins");
    RVec<float> out(2);
    // loop over dijets
    for (int i=0; i<pt.size(); i++) {
	float i_pt = pt[i];
	float i_msd = msd[i];
    	// find corresponding pT bin
    	int pt_bin = hist->GetYaxis()->FindFixBin(i_pt);
    	if (pt_bin > hist->GetYaxis()->GetNbins()){pt_bin = hist->GetYaxis()->GetNbins();}
    	else if (pt_bin <= 0){pt_bin = 1;}
    	// obtain corresponding rho bin
    	double rho = 2*TMath::Log(i_msd/i_pt);
    	int rho_bin = hist->GetXaxis()->FindFixBin(rho);
    	if (rho_bin > hist->GetXaxis()->GetNbins()){rho_bin=hist->GetXaxis()->GetNbins();}
    	else if (rho_bin <=0){rho_bin = 1;}
    	// obtain value of decorrelated discriminator
    	double ddt_disc = hist->GetBinContent(rho_bin,pt_bin);
	out[i] = ddt_disc;
    }
    return out;
}
