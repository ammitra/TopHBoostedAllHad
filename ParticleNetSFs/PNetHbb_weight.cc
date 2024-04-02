#include "TFile.h"
#include "TH2F.h"
#include <ROOT/RVec.hxx>
#include <string>
#include <set>
#include <algorithm>
#include <math.h>
#include "common.h"

class PNetHbb_weight {
    private:
	std::string _effmapname;	// name of the efficiency map ROOT file
	std::string _year;		// "16", "16APV", "17", "18"
	TFile * _effroot;		// pointer to the efficiency map file
	TH2F * _effmap;			// pointer to the efficiency map histo
	float _wp;			// Hbb working point delineating Faill/Pass (e.g 0.98)
        int _target_flavor;             // Flavor of jet to implement SF for (0: top, 2: bq, 4: Higgs)
        std::set<int> _other;           // Flavors of jets to consider for "other" classification/SF application
	/* --------------------------------------------------------------------------------------------------------
	 * Scale factors. To be read as SF[pt][variation], where variations are 0:nominal, 1:up, 2:down
	 * WP (tight) [0.98, 1.0]
	 */
        // HIGGS JET SF'S: pT cats are [400, 600), [600, 800), [800, +inf) across all years
        std::vector<std::vector<float>> SF2016APV_h = {{1.163,1.437,0.949},{1.206,1.529,0.924},{1.491,2.083,0.909}};
        std::vector<std::vector<float>> SF2016_h    = {{1.012,1.180,0.899},{1.247,1.509,0.999},{1.188,1.424,0.960}};
        std::vector<std::vector<float>> SF2017_h    = {{0.946,1.075,0.830},{1.027,1.158,0.880},{0.900,1.026,0.752}};
        std::vector<std::vector<float>> SF2018_h    = {{1.020,1.146,0.894},{1.013,1.110,0.912},{1.082,1.240,0.961}};
        // TOP JET SF'S: pT cats are [300, 450), [450, 600), [600, +inf)
        std::vector<std::vector<float>> SF2016APV_t = {{0.807,0.942,0.679},{0.763,0.871,0.657},{0.664,0.816,0.523}};
        std::vector<std::vector<float>> SF2016_t    = {{0.920,1.075,0.775},{0.930,1.056,0.810},{1.045,1.242,0.864}};
        std::vector<std::vector<float>> SF2017_t    = {{0.691,0.807,0.580},{1.055,1.144,0.969},{1.143,1.278,1.014}};
        std::vector<std::vector<float>> SF2018_t    = {{0.738,0.819,0.660},{0.977,1.040,0.917},{1.014,1.123,0.910}};
        // BQ JET SF'S: pT cats are [300, 450), [450, 600), [600, +inf)
	std::vector<std::vector<float>> SF2016APV_bq = {{1.284,1.428,1.154},{1.261,1.442,1.097},{0.879,1.309,0.531}};
	std::vector<std::vector<float>> SF2016_bq    = {{1.154,1.302,1.022},{0.962,1.152,0.797},{1.116,1.634,0.708}};
	std::vector<std::vector<float>> SF2017_bq    = {{1.275,1.395,1.165},{1.333,1.475,1.202},{1.440,1.773,1.170}};
	std::vector<std::vector<float>> SF2018_bq    = {{1.558,1.682,1.442},{1.349,1.476,1.233},{1.555,1.933,1.242}};

	// get the efficiency from efficiency map based on jet's pT and eta (for given flavor)
	float GetMCEfficiency(float pt, float eta, int flavor);
	// get the scale factor based on pT bin and internal year + tagger category variables (for given flavor)
	std::vector<float> GetScaleFactors(float pt, int flavor);

    public:
	// pass in year and path of eff map
	PNetHbb_weight(std::string year, std::string effmapname, float wp, int target_flavor, std::set<int> other = {1,3});
	~PNetHbb_weight();
	// Return a vector of weights for each event: {nom,up,down}
	RVec<float> eval(float Higgs_pt, float Higgs_eta, float Higgs_PNetHbbScore, int Higgs_jetFlavor);	
};

// Constructor - set year and load eff map in memory, 
PNetHbb_weight::PNetHbb_weight(std::string year, std::string effmapname, float wp, int target_flavor, std::set<int> other):_effmapname(effmapname),_year(year),_wp(wp),_target_flavor(target_flavor),_other(other) {
    // Change this logic yourself based on how you made the efficiency map.
    // I am assuming that it is one ROOT file per year, with one histogram.
    _effroot = hardware::Open(_effmapname, false);
    _effmap = (TH2F*)_effroot->Get("ratio");
};

// Close files on destruction
PNetHbb_weight::~PNetHbb_weight() {
    _effroot->Close();
};

// Get the MC effieciency of the jets in the given (pT, eta) bin
float PNetHbb_weight::GetMCEfficiency(float pt, float eta, int flavor) {
    // Efficiency map binned in pT: [60,0,3000], eta: [24,-2.4,2.4]
    int xbin = (int)(pt*30./3000.);
    int ybin = (int)((eta+2.4)*24/4.8);
    return _effmap->GetBinContent(xbin,ybin);
};

// Get the SF for the jet based on its pT and score and (internal) variation
std::vector<float> PNetHbb_weight::GetScaleFactors(float pt, int flavor) {
    // Output: {SF, SF_up, SF_down}
    // First check which pT bin we're in
    int ptBin;
    if (pt >= 300 && pt < 450) {ptBin = 0;}
    else if (pt >= 450 && pt < 600) {ptBin = 1;}
    else if (pt >= 600) {ptBin = 2;}

    std::vector<float> SF;

    if (flavor != _target_flavor) {
        SF = {1,1,1};
    }

    else { 
        if (flavor == 4 && pt > 400) { // SF's for merged Higgs jet
	    // separate pt bins for these SF's
	    if (pt >= 400 && pt < 600) {ptBin = 0;}
       	    else if (pt >= 600 && pt < 800) {ptBin = 1;}
	    else if (pt >= 800) {ptBin = 2;}

 	    // Now check year (this can prob all be done much more elegantly)
	    if (_year == "16") {SF = SF2016_h[ptBin];}
	    else if (_year == "16APV") {SF = SF2016APV_h[ptBin];}
	    else if (_year == "17") {SF = SF2017_h[ptBin];}
            else {SF = SF2018_h[ptBin];} // _year = "18"
        }

        else if (flavor == 0) { // SF's for merged top jet
            if (_year == "16") {SF = SF2016_t[ptBin];}
            else if (_year == "16APV") {SF = SF2016APV_t[ptBin];}
            else if (_year == "17") {SF = SF2017_t[ptBin];}
            else {SF = SF2018_t[ptBin];} // _year = "18"
        }

        else if (flavor == 2) { // SF's for merged bq jet
            if (_year == "16") {SF = SF2016_bq[ptBin];}
            else if (_year == "16APV") {SF = SF2016APV_bq[ptBin];}
            else if (_year == "17") {SF = SF2017_bq[ptBin];}
            else {SF = SF2018_bq[ptBin];} // _year = "18"
        }

        else {SF = {1,1,1};} 

    }
    return SF;
};

RVec<float> PNetHbb_weight::eval(float Higgs_pt, float Higgs_eta, float Higgs_PNetHbbScore, int Higgs_jetFlavor) {
    // Prepare the vector of weights to return
    RVec<float> out(3);

    float HbbTagEventWeight; 	// final multiplicative factor
    float eff;               	// eff(pt, eta, flavor)
    std::vector<float> SF;      // SF(pt, flavor), {SF, SF_up, SF_down}
    // get SF's and MC efficiency for this particular jet
    SF = GetScaleFactors(Higgs_pt, Higgs_jetFlavor);
    eff = GetMCEfficiency(Higgs_pt, Higgs_eta, Higgs_jetFlavor);
    for (int i : {0,1,2}) { // {nominal, up, down}
        float MC_tagged = 1.0,  MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;
        if (Higgs_PNetHbbScore > _wp) {  // PASS
            //MC_tagged *= eff;
            //data_tagged *= SF[i]*eff;
            data_tagged *= SF[i];
        }
        else {  // FAIL
            if (eff == 1) {eff = 0.99;} // Prevent the event weight from becoming undefined
            MC_notTagged *= (1 - eff);
            data_notTagged *= (1 - SF[i]*eff);
        }
        // Calculate the event weight for this variation
        HbbTagEventWeight = (data_tagged*data_notTagged) / (MC_tagged*MC_notTagged);
        out[i] = HbbTagEventWeight;

    } // end loop over variations

    // Send it {weight_nom, weight_up, weight_down}
    return out;
};
