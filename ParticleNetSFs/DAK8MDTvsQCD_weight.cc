#include "TFile.h"
#include "TH2F.h"
#include <ROOT/RVec.hxx>
#include <string>
#include <set>
#include <algorithm>
#include <math.h>
#include "common.h"

class DAK8MDTvsQCD_weight {
    private:
        std::string _effmapname;        // name of the efficiency map ROOT file
        std::string _year;              // "16", "16APV", "17", "18"
        TFile * _effroot;               // pointer to the efficiency map file
        TH2F * _effmap;                 // pointer to the efficiency map histo
        float _wp;                      // PNet TvsQCD working point delineating Fail/Pass
	/* -------------------------------------------------------------------------------------------------------
	 * Scale factors. To be read as SF[pt][variation], where variations are 0:nominal, 1:up, 2:down
	 * 0.5% mistag rate, pt bins: [300,400], [400,480], [480,600], [600,1200]
	 * https://twiki.cern.ch/twiki/bin/viewauth/CMS/DeepAK8Tagging2018WPsSFs#DeepAK8_MD_Top_quark_tagging
	 * Same SFs for 2016, 2016APV? (assume not measured for APV)
	 */
	std::vector<std::vector<float>> SF2016APV = {{0.89,0.97,0.81},{1.02,1.07,0.97},{0.93,0.97,0.89},{1.00,1.05,0.95}};
        std::vector<std::vector<float>> SF2016	  = {{0.89,0.97,0.81},{1.02,1.07,0.97},{0.93,0.97,0.89},{1.00,1.05,0.95}};
        std::vector<std::vector<float>> SF2017	  = {{0.95,1.01,0.89},{1.00,1.04,0.96},{0.98,1.02,0.94},{0.98,1.02,0.94}};
        std::vector<std::vector<float>> SF2018    = {{0.90,0.95,0.85},{0.97,1.00,0.94},{0.98,1.01,0.95},{0.95,0.98,0.92}};

        // get the efficiency from efficiency map based on jet's pT and eta (for given flavor)
        float GetMCEfficiency(float pt, float eta, int flavor);
        // get the scale factor based on pT bin and internal year + tagger category variables (for given flavor)
        std::vector<float> GetScaleFactors(float pt, int flavor);

    public:
        // pass in year and path of eff map
        DAK8MDTvsQCD_weight(std::string year, std::string effmapname, float wp);
        ~DAK8MDTvsQCD_weight();
        // Return a vector of weights for each event: {nom,up,down}
        RVec<float> eval(float Top_pt, float Top_eta, float Top_DAK8MDTvsQCDScore);
};

DAK8MDTvsQCD_weight::DAK8MDTvsQCD_weight(std::string year, std::string effmapname, float wp) : _effmapname(effmapname),_year(year),_wp(wp) {
    // Change this logic yourself based on how you made the efficiency map.
    // I am assuming that it is one ROOT file per year, with one histogram.
    _effroot = hardware::Open(_effmapname, false);
    _effmap = (TH2F*)_effroot->Get("ratio");
};

DAK8MDTvsQCD_weight::~DAK8MDTvsQCD_weight() {
    _effroot->Close();
};

DAK8MDTvsQCD_weight::GetMCEfficiency(float pt, float eta, int flavor) {
    // Efficiency map binned in pT: [60,0,3000], eta: [24,-2.4,2.4]
    int xbin = (int)(pt*30./3000.);
    int ybin = (int)((eta+2.4)*24/4.8);
    return _effmap->GetBinContent(xbin,ybin);
};

// Get the SFs (nom/up/down) for the jet based on its pT
std::vector<float> DAK8MDTvsQCD_weight::GetScaleFactors(float pt) {
    // Output: {SF, SF_up, SF_down}
    // First check which pT bin we're in
    int ptBin;
    if 		(pt >= 300 && pt < 400) {ptBin = 0;}
    else if 	(pt >= 400 && pt < 480) {ptBin = 1;}
    else if	(pt >= 480 && pt < 600) {ptBin = 2;}
    else if 	(pt >= 600) {ptBin = 3;}

    std::vector<float> SF;

    if (_year == "16") {
	SF = SF2016[ptBin];
    }
    else if (_year == "16APV") {
	SF = SF2016APV[ptBin];
    }
    else if (_year == "17") {
	SF = SF2017[ptBin];
    }
    else if (_year == "18") {
	SF = SF2018[ptBin];
    }
    else {
	std::cout << "ERROR\n";
    }
    
    return SF;
};

DAK8MDTvsQCD_weight::eval(float Top_pt, float Top_eta, float Top_DAK8MDTvsQCDScore) {
    RVec<float> out(3);
    float TvsQCDEventWeight;  	// final multiplicative event weight
    float eff;		    	// eff(pt, eta)
    std::vector<float> SF;	// SF(pt), {SF, SF_up, SF_down}

    SF  = GetScaleFactors(Top_pt);
    eff = GetMCEfficiency(Top_pt, Top_eta);
    for (int i : {0,1,2}) { // {nominal, up, down}
        float MC_tagged = 1.0,  MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;
    	if (Top_DAK8MDTvsQCDScore > _wp) {	// PASS
	    data_tagged *= SF[i];
    	}
    	else {	// FAIL
            if (eff == 1) {eff = 0.99;} // Prevent the event weight from becoming undefined
            MC_notTagged *= (1 - eff);
            data_notTagged *= (1 - SF[i]*eff);
    	}
    	// calculate final event weight
    	TvsQCDEventWeight = (data_tagged*data_notTagged) / (MC_tagged*MC_notTagged);
	out[i] = HbbTagEventWeight;
    }
    return out;
};
