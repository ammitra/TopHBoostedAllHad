#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <TFile.h>
#include <TH2F.h>

using namespace ROOT::VecOps;

/**
 * IMPORTANT - this class is used *after* the two W candidates have been identified and new SubCollections
 * have been made for the top/phi candidates. Therefore we are no longer passing in RVecs but rather single
 * values to most methods.
 *
 * This class is meant to apply DeepAK8MD_TvsQCD to the Phi candidate jet in the ttbarCR to TTBAR MC ONLY
 */
class DAK8PhiSFHandler {
    private:
        std::string _year;      // "16", "16APV", "17", "18"
        TFile*      _effroot;   // store pointer to efficiency file
        std::string _wp_str;    // DAK8MD Top tagger working point (e.g 0.889 -> 889)
        float       _wp;        // DAK8MD Top tagger working point (e.g 0.889)
        TRandom3*   _rand;      // random number generator
        // DAK8MD top tagging SFs
        // https://twiki.cern.ch/twiki/bin/viewauth/CMS/DeepAK8Tagging2018WPsSFs#DeepAK8_MD_Top_quark_tagging
        // pt categories: [300, 400), [400, 480), [480, 600), [600, 1200)
        std::vector<std::vector<float>> SF2016_dak8    = {{0.92,1.04,0.81},{1.01,1.18,0.84},{0.84,0.90,0.78},{1.00,1.07,0.94}};
        std::vector<std::vector<float>> SF2017_dak8    = {{0.88,0.96,0.80},{0.90,0.95,0.85},{0.95,1.00,0.90},{0.97,1.03,0.91}};
        std::vector<std::vector<float>> SF2018_dak8    = {{0.81,0.88,0.74},{0.93,0.98,0.88},{0.96,1.02,0.92},{0.93,0.98,0.88}};

        // Helper functions
        int   GetPtBin(float pt);
        float GetSF(float pt, int variation);
        float GetEff(float pt, float eta, int jetCat);
        int   GetOriginalCat(float taggerScore);
    public:
        DAK8PhiSFHandler(std::string year, std::string effpath, std::string wp_str, float wp, int seed);
        ~DAK8PhiSFHandler();
        // MAIN METHODS
        // returns the status of the jet (0: not top-tagged, 1: DAK8 top-tagged)
        int GetNewTopCat(float DAK8_discriminant, float pt, float eta, int variation, int jetCat);
};

DAK8PhiSFHandler::DAK8PhiSFHandler(std::string year, std::string effpath, std::string wp_str, float wp, int seed) : _year(year), _wp(wp), _wp_str(wp_str) {
    _effroot = TFile::Open(effpath.c_str(),"READ");
    _rand = new TRandom3(seed);
};

DAK8PhiSFHandler::~DAK8PhiSFHandler() {
    _effroot->Close();
    delete _rand;  
};

int DAK8PhiSFHandler::GetPtBin(float pt) {
    int ptBin;
    if          (pt >= 300 && pt < 400) { ptBin = 0; }
    else if     (pt >= 400 && pt < 480) { ptBin = 1; }
    else if     (pt >= 480 && pt < 600) { ptBin = 2; }
    else if     (pt >= 600) { ptBin = 3; }
    else        { ptBin = 0; }
    return ptBin;
};

float DAK8PhiSFHandler::GetSF(float pt, int variation) {
    float SF;
    int ptBin = GetPtBin(pt);
    int var = variation;
    if ( (_year == "16APV") || (_year == "16") ) {
        SF = SF2016_dak8[ptBin][var];
    }
    else if (_year == "17") {
        SF = SF2017_dak8[ptBin][var];
    }
    else if (_year == "18") {
        SF = SF2018_dak8[ptBin][var];
    }
    return SF;
};

float DAK8PhiSFHandler::GetEff(float pt, float eta, int jetCat) {
    float eff;
    TEfficiency* _effmap;
    int cat = jetCat;   // 0: other, 1: qq, 2: bq, 3: bqq
    // Determine the histogram name
    // Higgs-matched_Dijet_deepTagMD_TvsQCD_WP0p889_TEff
    std::string histname_base ("Dijet_deepTagMD_TvsQCD_WP0p");
    if (cat == 0) {
        std::string histname = "other-matched_" + histname_base + _wp_str + "_TEff";
        _effmap = (TEfficiency*)_effroot->Get(histname.c_str());
    }
    else if (cat == 1) {
        std::string histname = "top_qq-matched_" + histname_base + _wp_str + "_TEff";
        _effmap = (TEfficiency*)_effroot->Get(histname.c_str());
    }
    else if (cat == 2) {
        std::string histname = "top_bq-matched_" + histname_base + _wp_str + "_TEff";
        _effmap = (TEfficiency*)_effroot->Get(histname.c_str());
    }
    else if (cat == 3) {
        std::string histname = "top_bqq-matched_" + histname_base + _wp_str + "_TEff";
        _effmap = (TEfficiency*)_effroot->Get(histname.c_str());
    }
    else {
        std::string histname = "other-matched_" + histname_base + _wp_str + "_TEff";
        _effmap = (TEfficiency*)_effroot->Get(histname.c_str());
    }
    int globalbin = _effmap->FindFixBin(pt, eta);
    eff = _effmap->GetEfficiency(globalbin);
    return eff;
};

int DAK8PhiSFHandler::GetOriginalCat(float taggerScore) {
    // determine whether the jet is originally tagged based on its score
    int isTagged;
    if (taggerScore > _wp) {
        isTagged = 1;
    }
    else {
        isTagged = 0;
    }
    return isTagged;
};

int DAK8PhiSFHandler::GetNewTopCat(float DAK8_discriminant, float pt, float eta, int variation, int jetCat) {
    int isTagged = GetOriginalCat(DAK8_discriminant);
    int newTag = isTagged;
    float SF = GetSF(pt, variation);
    float eff = GetEff(pt, eta, jetCat);
    if (eff == 1.0) { eff = 0.99; }
    if (eff == 0.0) { eff = 0.0000001; }
    if (SF == 1) { return newTag; }
    float rand = _rand->Uniform(1.0);
    if (SF > 1) {
        if ( isTagged == 0) {
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
        if ( isTagged == 1 && rand > SF) {
            newTag = 0;
        }
    }
    return newTag;
};
