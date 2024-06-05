#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <TFile.h>
#include <TH2F.h>

using namespace ROOT::VecOps;

class PNetWqqSFHandler {
    private:
	// Internal variables
	std::string 	_year;		// "16", "16APV", "17", "18"
	std::string	_category;	// "signal", "ttbar", "other"
	TFile* 		_effroot;	// store pointer to efficiency file
	float		_wp;		// tagger working point
	TRandom3*	_rand;		// random number generator

  	// W tagging scale factors ------------------------------------------------------------------------
  	// pt categories: [200, 300), [300, 400), [400, +inf)		{nom, up, down}
        std::vector<std::vector<float>> SF2016APV = {{0.90,0.93,0.87},{0.87,0.91,0.83},{0.86,0.94,0.78}};
        std::vector<std::vector<float>> SF2016    = {{0.89,0.93,0.86},{0.86,0.90,0.82},{0.73,0.80,0.64}};
        std::vector<std::vector<float>> SF2017    = {{0.91,0.93,0.89},{0.90,0.93,0.87},{0.89,0.94,0.85}};
        std::vector<std::vector<float>> SF2018    = {{0.87,0.89,0.85},{0.86,0.88,0.84},{0.82,0.86,0.78}};

	// top mistagging scale factors -------------------------------------------------------------------
	// pt categories: [300,450), [450,600), [600,+inf)		{nom, up, down}
	// TOP MERGED : bqq
        std::vector<std::vector<float>> SF2016APV_t = {{0.992,1.055,0.929},{0.972,1.029,0.915},{1.002,1.103,0.902}};
        std::vector<std::vector<float>> SF2016_t    = {{0.839,0.907,0.773},{1.001,1.062,0.941},{1.048,1.144,0.956}};
        std::vector<std::vector<float>> SF2017_t    = {{1.100,1.160,1.041},{1.027,1.070,0.985},{1.154,1.221,1.087}};
        std::vector<std::vector<float>> SF2018_t    = {{1.055,1.094,1.017},{1.015,1.046,0.984},{0.967,1.025,0.911}};
	// W MERGED : qq
        std::vector<std::vector<float>> SF2016APV_w = {{1.004,1.091,0.928},{1.247,1.425,1.103},{0.723,0.952,0.546}};
        std::vector<std::vector<float>> SF2016_w    = {{1.035,1.160,0.933},{0.869,1.003,0.758},{1.301,1.696,1.014}};
        std::vector<std::vector<float>> SF2017_w    = {{1.019,1.101,0.947},{0.800,0.847,0.756},{0.877,1.018,0.750}};
        std::vector<std::vector<float>> SF2018_w    = {{0.784,0.829,0.743},{0.783,0.826,0.743},{0.755,0.855,0.670}};
	// OTHER:
        std::vector<std::vector<float>> SF2016APV_o = {{1.025,1.060,0.990},{1.024,1.070,0.978},{1.242,1.333,1.152}};
        std::vector<std::vector<float>> SF2016_o    = {{0.988,1.026,0.950},{0.968,1.015,0.921},{1.008,1.104,0.915}};
        std::vector<std::vector<float>> SF2017_o    = {{1.016,1.054,0.979},{1.191,1.228,1.155},{1.192,1.260,1.127}};
        std::vector<std::vector<float>> SF2018_o    = {{1.080,1.111,1.049},{1.125,1.154,1.096},{1.270,1.329,1.212}};

	// Helper functions
	RVec<int> WhichJetIsWhich(bool isW0, bool isW1, bool isW2, RVec<float> WTagger, int idx0, int idx1, int idx2);
	int GetPtBin(float pt);	// will be called by GetSF()
	float GetSF(float pt, int variation, int jetCat);
	float GetEff(float pt, float eta, int jetCat);
	int GetNewWCat(int isTagged, float pt, float eta, int variation, int jetCat);	// will call GetSF() and GetEff()
	int GetOriginalCat(float taggerScore);

    public:
	PNetWqqSFHandler(std::string year, std::string category, std::string effpath, float wp, int seed);
	~PNetWqqSFHandler();
	RVec<int> Pick_W_candidates(RVec<float> Wqq_discriminant, RVec<float> corrected_pt, RVec<float> trijet_eta, RVec<float> corrected_mass, RVec<int> jetCats, int WqqSFVariation, bool invert, RVec<float> massWindow, RVec<int> idxs);
};

PNetWqqSFHandler::PNetWqqSFHandler(std::string year, std::string category, std::string effpath, float wp, int seed) : _year(year), _category(category), _wp(wp) {
    // Open the efficiency map for this process, instantiate a new TRandom3
    _effroot = TFile::Open(effpath.c_str(),"READ");
    _rand = new TRandom3(seed);
};

PNetWqqSFHandler::~PNetWqqSFHandler() {
   // Close the TFile, delete the TRandom3 instantiated with "new"
   _effroot->Close();
   delete _rand;
};

int PNetWqqSFHandler::GetPtBin(float pt) {
    // pT binning differs for signal and mistagging SFs - handle that here
    int ptBin;
    if (_category == "signal") {
	if 	(pt >= 200 && pt < 300) { ptBin=0; }
	else if (pt >= 300 && pt < 400) { ptBin=1; }
	else if (pt >= 400) { ptBin=2; }
        else    { ptBin = 0; }
    }
    else {
	if	(pt >= 300 && pt < 450) { ptBin=0; }
	else if (pt >= 450 && pt < 600) { ptBin=1; }
	else if (pt >= 600) { ptBin=2; }
        else    { ptBin = 0; }
    }
    return ptBin;
}

float PNetWqqSFHandler::GetSF(float pt, int variation, int jetCat) {
    // Obtain the SF for this jet based on whether we are handling signal or ttbar
    float SF;
    int ptBin 	 = GetPtBin(pt);
    int var   	 = variation;	// 0:nom, 1:up, 2:down
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
    int ttJetCat = jetCat;	// only used for ttbar

    if (_category == "signal") {
	if (_year == "16APV") {
	    SF = SF2016APV[ptBin][var];
	}
	else if (_year == "16") {
	    SF = SF2016[ptBin][var];
	}
	else if (_year == "17") {
	    SF = SF2017[ptBin][var];
	}
	else {
	    SF = SF2018[ptBin][var];
	}
    }
    else if (_category == "ttbar") {
        if (_year == "16APV") {
	    if (ttJetCat == 0) {
		SF = SF2016APV_o[ptBin][var];
	    }
	    else if (ttJetCat == 1) {
		SF = SF2016APV_w[ptBin][var];
	    }
	    else if (ttJetCat == 2) {
		SF = SF2016APV_w[ptBin][var];
	    }
	    else if (ttJetCat == 3) {
		SF = SF2016APV_t[ptBin][var];
	    }
	    else {
		SF = 1.0;
	    }
        }
        else if (_year == "16") {
            if (ttJetCat == 0) {
                SF = SF2016_o[ptBin][var];
            }
            else if (ttJetCat == 1) {
                SF = SF2016_w[ptBin][var];
            }
            else if (ttJetCat == 2) {
                SF = SF2016_w[ptBin][var];
            }
            else if (ttJetCat == 3) {
                SF = SF2016_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else if (_year == "17") {
            if (ttJetCat == 0) {
                SF = SF2017_o[ptBin][var];
            }
            else if (ttJetCat == 1) {
                SF = SF2017_w[ptBin][var];
            }
            else if (ttJetCat == 2) {
                SF = SF2017_w[ptBin][var];
            }
            else if (ttJetCat == 3) {
                SF = SF2017_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else {
            if (ttJetCat == 0) {
                SF = SF2018_o[ptBin][var];
            }
            else if (ttJetCat == 1) {
                SF = SF2018_w[ptBin][var];
            }
            else if (ttJetCat == 2) {
                SF = SF2018_w[ptBin][var];
            }
            else if (ttJetCat == 3) {
                SF = SF2018_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
    }
    return SF;
};

float PNetWqqSFHandler::GetEff(float pt, float eta, int jetCat) {
    // Obtain the efficiency for the given jet based on its top merging category (if ttbar) or W matching if signal
    // Efficiency map binned in pT: [60,0,3000], eta: [12,-2.4,2.4]
    float eff;
    TEfficiency* _effmap;
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
    int cat = jetCat;

    if (_category == "signal") {
	_effmap = (TEfficiency*)_effroot->Get("W-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
    }
    else if (_category == "ttbar") {
        if (cat == 0) {
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else if (cat == 1) {
            _effmap = (TEfficiency*)_effroot->Get("top_qq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else if (cat == 2) {
            _effmap = (TEfficiency*)_effroot->Get("top_bq-matched_Trijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
        else if (cat == 3) {
            _effmap = (TEfficiency*)_effroot->Get("top_bqq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else { // 4, 5 correspond to Higgs, W (not from top), so just make these other? 
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
    }
    int globalbin = _effmap->FindFixBin(pt, eta);
    eff = _effmap->GetEfficiency(globalbin);
    return eff;
};

/**
 * Takes in the original tagging status (if jet passes tagging WP or not).
 * Takes in a jet's pt and eta, calculates the respective scale factor and efficiency, and returns:
 * 	0: is not tagged (demoted)
 *	1: is tagged	 (promoted)
 */
int PNetWqqSFHandler::GetNewWCat(int isTagged, float pt, float eta, int variation, int jetCat) {
    int newTag = isTagged;
    float SF;
    float eff;
    // calculate SF for this jet
    SF = GetSF(pt, variation, jetCat);
    // calculate efficiency for this jet
    eff = GetEff(pt, eta, jetCat);
    if (eff == 1.0) { eff = 0.99; }	// avoid division by zero if SF > 1
    if (eff == 0.0) { eff = 0.00001; }
    // Main logic
    if (SF == 1) { return newTag; }	// no correction needed
    float rand = _rand->Uniform(1.0);
    if (SF > 1) {
        if ( isTagged == 0 ) {
            // fraction of jets that need to be upgraded
            float mistagPercent = (1.0 - SF) / (1.0 - (1.0/eff));
            // upgrade to tagged
            if (rand < mistagPercent) {
                newTag = 1;
            }
        }
    }
    else {
        // downgrade tagged to untagged
        if ( isTagged == 0 && rand > SF) {
            newTag = 0;
        }
    }
    return newTag;
};

int PNetWqqSFHandler::GetOriginalCat(float taggerScore) {
    // Determine whether the jet is originally tagged based on its score
    int isTagged;
    if (taggerScore > _wp) {
        isTagged = 1;
    }
    else {
	isTagged = 0;
    }
    return isTagged;
};

/**
 * Picks the two (anti)W candidates for each event in the SR or CR. If signal, applies W tagging SFs. 
 * If ttbar, applies W mistagging scale factors based on the top jet's merging status. 
 * If neither signal nor ttbar, just use raw MD_WvsQCD score and the W mass to identify the Ws. 
 */
RVec<int> PNetWqqSFHandler::Pick_W_candidates(RVec<float> Wqq_discriminant, RVec<float> corrected_pt, RVec<float> trijet_eta, RVec<float> corrected_mass, RVec<int> jetCats, int WqqSFVariation, bool invert, RVec<float> massWindow, RVec<int> idxs) {
    if (idxs.size() > 3) {
	std::cout << "PNetWqqSFHandler::Pick_W_candidates() -- WARNING: you have input more than 3 indices. Only 3 accepted. Assuming first three indices.\n";
    }
    RVec<int> out;	// vector containing the indices of the W candidates
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    bool isW0, isW1, isW2;

    // Split the logic based on which sample we're running on
    if ((_category == "signal") || (_category == "ttbar")) {
	// First, determine the original tagger category for each of the three jets based on Wqq working pt
	// 0: not W-tagged, 1: is W-tagged
	int orig_score0 = GetOriginalCat(Wqq_discriminant[idx0]);
        int orig_score1 = GetOriginalCat(Wqq_discriminant[idx1]);
        int orig_score2 = GetOriginalCat(Wqq_discriminant[idx2]);
	// Now determine new tagger category
	int new_score0 = GetNewWCat(orig_score0, corrected_pt[idx0], trijet_eta[idx0], WqqSFVariation, jetCats[idx0]);
        int new_score1 = GetNewWCat(orig_score1, corrected_pt[idx1], trijet_eta[idx1], WqqSFVariation, jetCats[idx1]);
        int new_score2 = GetNewWCat(orig_score2, corrected_pt[idx2], trijet_eta[idx2], WqqSFVariation, jetCats[idx2]);
	// logic to determine W selection using the new tagger "scores" (categories - 0:not tagged, 1:tagged)
	if (!invert) { // SIGNAL REGION - tagged (BUT APPLY MASS WINDOW LATER)
	    isW0 = (new_score0 == 1);
            isW1 = (new_score1 == 1);
            isW2 = (new_score2 == 1);
	}
	else { // CONTROL REGION
            isW0 = (new_score0 == 0);
            isW1 = (new_score1 == 0);
            isW2 = (new_score2 == 0);
	}
    }
    else if (_category == "other") { 
	// If not ttbar or signal, running on data or V+jets (or some non-dominant bkg where mistagging doesn't really matter.
	// Therefore, just do normal W identification based on the tagger score and the W mass window
	if (!invert) {	// SIGNAL REGION - tagged and within mass window
            isW0 = (Wqq_discriminant[idx0] > _wp);
            isW1 = (Wqq_discriminant[idx1] > _wp);
            isW2 = (Wqq_discriminant[idx2] > _wp);
	}
	else {	// CONTROL REGION
	    isW0 = (Wqq_discriminant[idx0] > 0.05) && (Wqq_discriminant[idx0] < _wp);	// > 0.05 to avoid huge statistics
            isW1 = (Wqq_discriminant[idx1] > 0.05) && (Wqq_discriminant[idx1] < _wp);
            isW2 = (Wqq_discriminant[idx2] > 0.05) && (Wqq_discriminant[idx2] < _wp);
	}
    }
    else {
	// this should never happen
	std::cout << "PNetWqqSFHandler::Pick_W_candidates() -- ERROR: only 'signal', 'ttbar', or 'other' are valid categories\n";
    }
    // determine the order of the return indices based on raw MD_WvsQCD score (highest first)
    out = WhichJetIsWhich(isW0, isW1, isW2, Wqq_discriminant, idx0, idx1, idx2);
    // return the indices of the newly picked (anti)W candidates and Higgs candidate
    return out;
};

RVec<int> PNetWqqSFHandler::WhichJetIsWhich(bool isW0, bool isW1, bool isW2, RVec<float> WTagger, int idx0, int idx1, int idx2) {
    RVec<int> out(3);
    // determine which is which
    if (isW0 && isW1 && isW2) { // all 3 jets pass W (anti)tagging - use raw W score to determine "real" W
        if (WTagger[idx0] < WTagger[idx1]) {
            if (WTagger[idx0] < WTagger[idx2]) {
                if (WTagger[idx1] < WTagger[idx2]) {
                    out[0] = idx2;      // highest W score
                    out[1] = idx1;      // middle W score
                    out[2] = idx0;      // lowest W score
                }
                else {
                    out[0] = idx1;
                    out[1] = idx2;
                    out[2] = idx0;
                }
            }
        }
        else {
            if (WTagger[idx1] < WTagger[idx2]) {
                if (WTagger[idx0] < WTagger[idx2]) {
                    out[0] = idx2;
                    out[1] = idx0;
                    out[2] = idx1;
                }
                else {
                    out[0] = idx0;
                    out[1] = idx2;
                    out[2] = idx1;
                }
            }
            else {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
        }
    }
    if ( (isW0 && isW1) || (isW0 && isW2) || (isW1 && isW2) ) { // 0 if less than 2 jets, 1 if 2 jets
        if (isW0 && isW1) {
            if (WTagger[idx0] > WTagger[idx1]) {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
            else {
                out[0] = idx1;
                out[1] = idx0;
                out[2] = idx2;
            }
        }
        else if (isW0 && isW2) {
            if (WTagger[idx0] > WTagger[idx2]) {
                out[0] = idx0;
                out[1] = idx2;
                out[2] = idx1;
            }
            else {
                out[0] = idx2;
                out[1] = idx0;
                out[2] = idx1;
            }
        }
        else {
            if (WTagger[idx1] > WTagger[idx2]) {
                out[0] = idx1;
                out[1] = idx2;
                out[2] = idx0;
            }
            else {
                out[0] = idx2;
                out[1] = idx1;
                out[2] = idx0;
            }
        }
    }
    else {      // less than 2 W jets tagged, return {-1, -1, -1}
        out[0] = -1;
        out[1] = -1;
        out[2] = -1;
    }
    return out;
};
