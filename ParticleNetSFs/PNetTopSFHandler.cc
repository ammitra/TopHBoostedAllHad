#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <TFile.h>
#include <TH2F.h>

using namespace ROOT::VecOps;

class PNetTopSFHandler {
    private:
        // Internal variables
        std::string     _year;          // "16", "16APV", "17", "18"
        std::string     _category;      // "signal", "ttbar", "other"
        TFile*          _effroot;       // store pointer to efficiency file
        float           _wp;            // tagger working point
        TRandom3*       _rand;          // random number generator

	// PNet Top tagging SFs - 0.1% mistagging rate
	// https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
	//  pt categories: [300, 400), [400, 480), [480, 600), [600, 1200)		{nom, up, down}
        std::vector<std::vector<float>> SF2016APV = {{1.10,1.18,1.02},{1.06,1.13,1.00},{1.04,1.11,0.98},{1.00,1.11,0.91}};
        std::vector<std::vector<float>> SF2016    = {{0.97,1.07,0.89},{0.91,0.96,0.86},{0.99,1.05,0.94},{1.00,1.09,0.92}};
        std::vector<std::vector<float>> SF2017    = {{1.12,1.24,1.02},{0.96,1.01,0.92},{1.00,1.05,0.95},{0.93,0.98,0.87}};
        std::vector<std::vector<float>> SF2018    = {{1.03,1.12,0.85},{0.95,1.00,0.91},{0.91,0.95,0.88},{0.95,1.02,0.90}};

	// Helper functions
        int   GetPtBin(float pt); // will be called by GetSF()
        float GetSF(float pt, int variation, int jetCat);
        float GetEff(float pt, float eta, int jetCat);
        int   GetNewTopCat(int isTagged, float pt, float eta, int variation, int jetCat);   // will call GetSF() and GetEff()
        int   GetOriginalCat(float taggerScore);

    public:
        PNetTopSFHandler(std::string year, std::string category, std::string effpath, float wp, int seed);
        ~PNetTopSFHandler();
        RVec<int> Pick_Top_candidate(RVec<float> TvsQCD_discriminant, RVec<float> HbbvsQCD_discriminant, RVec<float> corrected_pt, RVec<float> dijet_eta, RVec<float> corrected_mass, RVec<int> jetCats, int TopSFVariation, bool invert, RVec<float> massWindow, RVec<int> idxs);
};

PNetTopSFHandler::PNetTopSFHandler(std::string year, std::string category, std::string effpath, float wp, int seed) : _year(year), _category(category), _wp(wp) {
    // Open the efficiency map for this process, instantiate a new TRandom3
    _effroot = TFile::Open(effpath.c_str(),"READ");
    _rand = new TRandom3(seed);
};

PNetTopSFHandler::~PNetTopSFHandler() {
    _effroot->Close();
    delete _rand;
};

int PNetTopSFHandler::GetPtBin(float pt) {
    // pT binning differs for signal (PNet) SFs - handle that here
    int ptBin;
    if      (pt >= 300 && pt < 400) { ptBin = 0; }
    else if (pt >= 400 && pt < 480) { ptBin = 1; }
    else if (pt >= 480 && pt < 600) { ptBin = 2; }
    else if (pt >= 600) { ptBin = 3; }
    else { ptBin = 0; }
    return ptBin;
};

float PNetTopSFHandler::GetSF(float pt, int variation, int jetCat) {
    float SF;
    int ptBin = GetPtBin(pt);
    int var   = variation;      // 0:nom, 1:up, 2:down
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
    return SF;
};

float PNetTopSFHandler::GetEff(float pt, float eta, int jetCat) {
    float eff;
    TEfficiency* _effmap;
    int cat = jetCat;
    if (cat == 0) {
        _effmap = (TEfficiency*)_effroot->Get("other-matched_Dijet_particleNet_TvsQCD_WP0p94_TEff");
    }
    else if (cat == 1) {
        _effmap = (TEfficiency*)_effroot->Get("top_qq-matched_Dijet_particleNet_TvsQCD_WP0p94_TEff");
    }
    else if (cat == 2) {
        _effmap = (TEfficiency*)_effroot->Get("top_bq-matched_Dijet_particleNet_TvsQCD_WP0p94_TEff");
    }
    else if (cat == 3) {
        _effmap = (TEfficiency*)_effroot->Get("top_bqq-matched_Dijet_particleNet_TvsQCD_WP0p94_TEff");
    }
    else {
        _effmap = (TEfficiency*)_effroot->Get("other-matched_Dijet_particleNet_TvsQCD_WP0p94_TEff");
    }
    int globalBin = _effmap->FindFixBin(pt, eta);
    eff = _effmap->GetEfficiency(globalBin);
    return eff;
};

/*
 * Takes in the original tagging status (if jet passes tagging WP or not).
 * Takes in a jet's pt and eta, calculates the respective scale factor and efficiency, and returns:
 *      0: is not tagged (demoted)
 *      1: is tagged     (promoted)
 */
int PNetTopSFHandler::GetNewTopCat(int isTagged, float pt, float eta, int variation, int jetCat) {
    int newTag = isTagged;
    float SF;
    float eff;
    // calculate SF and efficiency for this jet
    SF  = GetSF(pt, variation, jetCat);
    eff = GetEff(pt, eta, jetCat);
    if (eff == 1.0) { eff = 0.99; }
    if (eff == 0.0) { eff = 0.00001; }
    // main logic
    if (SF == 1) { return newTag; }     // no correction needed
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
        if ( isTagged == 1 && rand > SF ) {
            newTag = 0;
        }
    }
    return newTag;
};

int PNetTopSFHandler::GetOriginalCat(float taggerScore) {
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

RVec<int> PNetTopSFHandler::Pick_Top_candidate(RVec<float> TvsQCD_discriminant, RVec<float> HbbvsQCD_discriminant, RVec<float> corrected_pt, RVec<float> dijet_eta, RVec<float> corrected_mass, RVec<int> jetCats, int TopSFVariation, bool invert, RVec<float> massWindow, RVec<int> idxs) {
    if (idxs.size() > 2) {
        std::cout << "PNetTopHandler::Pick_Top_candidate() -- WARNING: you have input more than 2 indices. Only 2 acceped. Assuming first two indices\n";
    }
    RVec<int> out(2);
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    float massLo = massWindow[0];
    float massHi = massWindow[1];

    // First, determine original tagger categories for each jet
    int orig_score0 = GetOriginalCat(TvsQCD_discriminant[idx0]);
    int orig_score1 = GetOriginalCat(TvsQCD_discriminant[idx1]);
    // Now determine new tagger category
    int new_score0 = GetNewTopCat(orig_score0, corrected_pt[idx0], dijet_eta[idx0], TopSFVariation, jetCats[idx0]);
    int new_score1 = GetNewTopCat(orig_score1, corrected_pt[idx1], dijet_eta[idx1], TopSFVariation, jetCats[idx1]);
    // logic to determine Top selection using the new tagger "scores" (categories - 0:not tagged, 1:tagged)
    bool isTop0, isTop1;
    if (!invert) {      // SIGNAL REGION
        // Apply SFs to signal...
        if (_category == "signal") {
            isTop0 = (new_score0 == 1);
            isTop1 = (new_score1 == 1);
        }
        // ...otherwise, use raw tagger scores
        else {
            isTop0 = (TvsQCD_discriminant[idx0] > _wp);
            isTop1 = (TvsQCD_discriminant[idx1] > _wp);
        }
    }
    else {      // CONTROL REGION - perform top mass window and Higgs veto in selection script and generate cutflow
        // Apply SFs to signal...
        if (_category == "signal") {
            //isTop0 = (new_score0 == 0) && (HbbvsQCD_discriminant[idx0] < 0.2) && (corrected_mass[idx0] > massWindow[0]) && (corrected_mass[idx0] < massWindow[1]);
            //isTop1 = (new_score1 == 0) && (HbbvsQCD_discriminant[idx1] < 0.2);
            isTop0 = (new_score0 == 0);
            isTop1 = (new_score1 == 0);
        }
        else {
            //isTop0 = (TvsQCD_discriminant[idx0] < _wp) && (TvsQCD_discriminant[idx0] > 0.2) && (HbbvsQCD_discriminant[idx0] < 0.2) && (corrected_mass[idx0] > massWindow[0]) && (corrected_mass[idx0] < massWindow[1]);
            //isTop1 = (TvsQCD_discriminant[idx0] < _wp) && (TvsQCD_discriminant[idx0] > 0.2) && (HbbvsQCD_discriminant[idx0] < 0.2);
            isTop0 = (TvsQCD_discriminant[idx0] < _wp) && (TvsQCD_discriminant[idx0] > 0.2);
            isTop1 = (TvsQCD_discriminant[idx0] < _wp) && (TvsQCD_discriminant[idx0] > 0.2);
        }
    }
    // Determine which is which
    if (isTop0 && isTop1) {
        // if both pass as Top, use the raw TvsQCD score to determine which is "real" top
        if (TvsQCD_discriminant[idx0] > TvsQCD_discriminant[idx1]) {
            out[0] = idx0;
            out[1] = idx1;
        }
        else {
            out[0] = idx1;
            out[1] = idx0;
        }
    }
    else if (isTop0) {
        out[0] = idx0;
        out[1] = idx1;
    }
    else if (isTop1) {
        out[0] = idx1;
        out[1] = idx0;
    }
    else {
        out[0] = -1;
        out[1] = -1;
    }
    return out;
};
