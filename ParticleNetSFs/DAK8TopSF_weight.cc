#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <vector>
#include <TFile.h>
#include <TH2F.h>
#include <TEfficiency.h>

using namespace ROOT::VecOps;

/* ----------------------------------------------------------------------------
 * DAK8SFHandler
 * ----------------------------------------------------------------------------
 *  Class for applying DAK8 MDTvsQCD scale factors to the ttbar Monte Carlo in
 *  the ttbar control region. 
 *  The SF application algorithm is taken from the BTV documentation Twiki:
 *  https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#1a_Event_reweighting_using_scale
 */ 
class DAK8TopSF_weight {
    private:
        std::string _year;      // "16", "16APV", "17", "18"
        TFile*      _effroot;   // store pointer to efficiency file
        std::string _wp_str;    // DAK8MD Top tagger working point (e.g 0.889 -> 889)
        float       _wp;        // DAK8MD Top tagger working point (e.g 0.889)
        // DAK8MD top tagging SFs
        // https://twiki.cern.ch/twiki/bin/viewauth/CMS/DeepAK8Tagging2018WPsSFs#DeepAK8_MD_Top_quark_tagging
        // pt categories: [300, 400), [400, 480), [480, 600), [600, 1200)
        // {nom, up, down}
        std::vector<std::vector<float>> SF2016_dak8    = {{0.92,1.04,0.81},{1.01,1.18,0.84},{0.84,0.90,0.78},{1.00,1.07,0.94}};
        std::vector<std::vector<float>> SF2017_dak8    = {{0.88,0.96,0.80},{0.90,0.95,0.85},{0.95,1.00,0.90},{0.97,1.03,0.91}};
        std::vector<std::vector<float>> SF2018_dak8    = {{0.81,0.88,0.74},{0.93,0.98,0.88},{0.96,1.02,0.92},{0.93,0.98,0.88}};

        // Helper functions
        int   GetPtBin(float pt);
        float GetSF(float pt, int variation);
        float GetEff(float pt, float eta, int jetCat);
    public:
        DAK8TopSF_weight(std::string year, std::string effpath, std::string wp_str, float wp);
        ~DAK8TopSF_weight();
        RVec<float> eval(RVec<float> pt, RVec<float> eta, RVec<float> DAK8_score, RVec<int> jetCat);
};

DAK8TopSF_weight::DAK8TopSF_weight(std::string year, std::string effpath, std::string wp_str, float wp) : _year(year), _wp_str(wp_str), _wp(wp) {
    _effroot = TFile::Open(effpath.c_str(), "READ");
};

DAK8TopSF_weight::~DAK8TopSF_weight() {
    _effroot->Close();
};

int DAK8TopSF_weight::GetPtBin(float pt) {
    int ptBin;
    if          (pt >= 300 && pt < 400) { ptBin = 0; }
    else if     (pt >= 400 && pt < 480) { ptBin = 1; }
    else if     (pt >= 480 && pt < 600) { ptBin = 2; }
    else if     (pt >= 600) { ptBin = 3; }
    else        { ptBin = 0; }
    return ptBin;
};

float DAK8TopSF_weight::GetSF(float pt, int variation) {
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

float DAK8TopSF_weight::GetEff(float pt, float eta, int jetCat) {
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
    delete _effmap;
    return eff;
};

RVec<float> DAK8TopSF_weight::eval(RVeC<float> pt, RVec<float> eta, RVec<float> DAK8_score, RVec<int> jetCat) {
    // Prepare the vector of weights to return
    RVec<float> out(3);
    // Loop over variations (0:nom, 1:up, 2:down)
    for (int var : {0,1,2}) {
        // event weight calculation variables
        float MC_tagged = 1.0, MC_notTagged = 1.0; 
        float data_tagged = 1.0, data_notTagged = 1.0;
        float DAK8_event_weight;
        // Loop over jets in the event (only two, since running on Dijet snapshots)
        for (int i=0; i<pt.size(); i++) {
            float SF, eff;
            // get the SF and efficiency for this particular jet.
            SF  = GetSF(pt[i], var);                    // the proper up/down/nom SF is picked by this function
            eff = GetEff(pt[i], eta[i], jetCat[i]);     // obtains the efficiency for the jet of a given MC truth for this tagger
            // Check if the jet is tagged at this particular WP - NOTE: This is different than the flavor (MC truth) of the jet
            if (DAK8_score[i] > _wp) {
                MC_tagged *= eff;
                data_tagged *= SF*eff;
            }
            else {
                MC_notTagged *= (1.-eff);
                data_notTagged *= (1.-SF*eff);
            }
        }
        // After looping over all jets, calculate the final event weight for this variation
        if ( (MC_tagged * MC_notTagged) == 0.0) {
            DAK8_event_weight = 1.0;
        }
        else {
            DAK8_event_weight = (data_tagged * data_notTagged) / (MC_tagged * MC_notTagged);
        }
        out[var] = DAK8_event_weight;
    }
    return out; // {nom, up, down}
};
