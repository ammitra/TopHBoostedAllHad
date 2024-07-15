#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <vector>
#include <TFile.h>
#include <TH2F.h>
#include <TEfficiency.h>

using namespace ROOT::VecOps;

class PNetXbbSF_weight {
    private:
        // Internal variables
        std::string _year;      // "16", "16APV", "17", "18"
        std::string _category;  // "signal", "ttbar" - applying TAGGING SFs to singal, MISTAGGING SFs to ttbar
        TFile*      _effroot;   // store pointer to efficiency file
        float _wp;              // PNet Hbb tagger working point
        // Higgs tagging scale factors ---------------------------------------------------------------------------------------
        // pt categories: [400, 600), [600, 800), [800, +inf)           {nom, up, down}
        std::vector<std::vector<float>> SF2016APV = {{1.163,1.437,0.949},{1.206,1.529,0.924},{1.491,2.083,0.909}};
        std::vector<std::vector<float>> SF2016    = {{1.012,1.180,0.899},{1.247,1.509,0.999},{1.188,1.424,0.960}};
        std::vector<std::vector<float>> SF2017    = {{0.946,1.075,0.830},{1.027,1.158,0.880},{0.900,1.026,0.752}};
        std::vector<std::vector<float>> SF2018    = {{1.020,1.146,0.894},{1.013,1.110,0.912},{1.082,1.240,0.961}};
        // PNet Hbb Top mistagging scale factors --------------------------------------------------------------------------------------
        // pt categories: [300, 450), [450, 600), [600, +inf)           {nom, up, down}
        // TOP MERGED: bqq
        std::vector<std::vector<float>> SF2016APV_t = {{0.807,0.942,0.679},{0.763,0.871,0.657},{0.664,0.816,0.523}};
        std::vector<std::vector<float>> SF2016_t    = {{0.920,1.075,0.775},{0.930,1.056,0.810},{1.045,1.242,0.864}};
        std::vector<std::vector<float>> SF2017_t    = {{0.691,0.807,0.580},{1.055,1.144,0.969},{1.143,1.278,1.014}};
        std::vector<std::vector<float>> SF2018_t    = {{0.738,0.819,0.660},{0.977,1.040,0.917},{1.014,1.123,0.910}};
        // other: bq, qq
        std::vector<std::vector<float>> SF2016APV_w = {{1.284,1.428,1.154},{1.261,1.442,1.097},{0.879,1.309,0.531}};
        std::vector<std::vector<float>> SF2016_w    = {{1.154,1.302,1.022},{0.962,1.152,0.797},{1.116,1.634,0.708}};
        std::vector<std::vector<float>> SF2017_w    = {{1.275,1.395,1.165},{1.333,1.475,1.202},{1.440,1.773,1.170}};
        std::vector<std::vector<float>> SF2018_w    = {{1.558,1.682,1.442},{1.349,1.476,1.233},{1.555,1.933,1.242}};
        // Helper functions
        int   GetPtBin(float pt);
        float GetSF(float pt, int variation, int jetCat);
        float GetEff(float pt, float eta, int jetCat);
    public:
        PNetXbbSF_weight(std::string year, std::string category, std::string effpath, float wp);
        ~PNetXbbSF_weight();
        RVec<float> eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetXbb_score, RVec<int> jetCat);
};

PNetXbbSF_weight::PNetXbbSF_weight(std::string year, std::string category, std::string effpath, float wp) : _year(year), _category(category), _wp(wp) {
    _effroot = TFile::Open(effpath.c_str(), "READ");
};

PNetXbbSF_weight::~PNetXbbSF_weight() {
    _effroot->Close();
};

int PNetXbbSF_weight::GetPtBin(float pt) {
    // pT binning differs for signal and mistagging SFs - handle that here
    int ptBin;
    if (_category == "signal") {        // PNet Hbb tagging SFs
        if      (pt >= 400 && pt < 600) { ptBin=0; }
        else if (pt >= 600 && pt < 800) { ptBin=1; }
        else if (pt >= 800) { ptBin=2; }
        else    { ptBin = 0; }
    }
    else if (_category == "ttbar") {    // PNet Hbb mistagging SFs
        if      (pt >= 300 && pt < 450) { ptBin=0; }
        else if (pt >= 450 && pt < 600) { ptBin=1; }
        else if (pt >= 600) { ptBin=2; }
        else    { ptBin = 0; }
    }
    return ptBin;
};

float PNetXbbSF_weight::GetSF(float pt, int variation, int jetCat) {
    // Obtain the SF for this jet based on whether we are handling signal or ttbar
    float SF;
    int ptBin = GetPtBin(pt);
    int var   = variation;   // 0:nom, 1:up, 2:down
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
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
    else if (_category == "ttbar") {        // we only want to apply mistagging SFs to ttbar in SR/CR
        if (_year == "16APV") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2016APV_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2016APV_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2016APV_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2016APV_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else if (_year == "16") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2016_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2016_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2016_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2016_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else if (_year == "17") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2017_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2017_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2017_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2017_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else {
            if (jetCat == 0) {
                SF = 1.0;//= SF2018_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2018_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2018_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2018_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
    }
    return SF;
};

float PNetXbbSF_weight::GetEff(float pt, float eta, int jetCat) {
    // Obtain the efficiency for the given jet based on its top merging category (if ttbar) or H matching if signal
    // Efficiency map binned in pT: [60,0,3000], eta: [12,-2.4,2.4]
    float eff;
    TEfficiency* _effmap;
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
    int cat = jetCat;

    if (_category == "signal") {
        _effmap = (TEfficiency*)_effroot->Get("Higgs-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
    }
    else if (_category == "ttbar") {
        if (cat == 0) {
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
        else if (cat == 1) {
            _effmap = (TEfficiency*)_effroot->Get("top_qq-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
        else if (cat == 2) {
            _effmap = (TEfficiency*)_effroot->Get("top_bq-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
        else if (cat == 3) {
            _effmap = (TEfficiency*)_effroot->Get("top_bqq-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
        else { // 4, 5 correspond to Higgs, W (not from top), so just make these other?
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Dijet_particleNetMD_HbbvsQCD_WP0p98_TEff");
        }
    }

    int globalbin = _effmap->FindFixBin(pt, eta);
    eff = _effmap->GetEfficiency(globalbin);
    delete _effmap;
    return eff;
};

RVec<float> PNetXbbSF_weight::eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetXbb_score, RVec<int> jetCat) {
    RVec<float> out(3);
    for (int var : {0,1,2}) {
        float MC_tagged = 1.0, MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;
        float PNetXbb_event_weight;
        for (int i=0; i<pt.size(); i++) {
            float SF, eff;
            SF  = GetSF(pt[i], var, jetCat[i]);
            eff = GetEff(pt[i], eta[i], jetCat[i]);
            if (PNetXbb_score[i] > _wp) {
                MC_tagged *= eff;
                data_tagged *= SF*eff;
            }
            else { 
                MC_notTagged *= (1.-eff);
                data_notTagged *= (1.-SF*eff);
            }
        }
        if ( (MC_tagged * MC_notTagged) == 0.0) {
            PNetXbb_event_weight = 1.0;
        }
        else {
            PNetXbb_event_weight = (data_tagged * data_notTagged) / (MC_tagged * MC_notTagged);
        }
        out[var] = PNetXbb_event_weight;
    }
    return out;
};
