#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <vector>
#include <TFile.h>
#include <TH2F.h>
#include <TEfficiency.h>

using namespace ROOT::VecOps;

class PNetTopSF_weight {
    private:
        std::string _year;      // "16", "16APV", "17", "18"
        TFile*      _effroot;   // store pointer to efficiency file
        float       _wp;        // PNet TvsQCD tagger working point

        // PNet Top tagging SFs - 0.1% mistagging rate
        // https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
        //  pt categories: [300, 400), [400, 480), [480, 600), [600, 1200)              {nom, up, down}
        std::vector<std::vector<float>> SF2016APV = {{1.10,1.18,1.02},{1.06,1.13,1.00},{1.04,1.11,0.98},{1.00,1.11,0.91}};
        std::vector<std::vector<float>> SF2016    = {{0.97,1.07,0.89},{0.91,0.96,0.86},{0.99,1.05,0.94},{1.00,1.09,0.92}};
        std::vector<std::vector<float>> SF2017    = {{1.12,1.24,1.02},{0.96,1.01,0.92},{1.00,1.05,0.95},{0.93,0.98,0.87}};
        std::vector<std::vector<float>> SF2018    = {{1.03,1.12,0.85},{0.95,1.00,0.91},{0.91,0.95,0.88},{0.95,1.02,0.90}};

        // helper functions
        int   GetPtBin(float pt);
        float GetSF(float pt, int variation);
        float GetEff(float pt, float eta, int jetCat);
    public:
        PNetTopSF_weight(std::string year, std::string effpath, float wp);
        ~PNetTopSF_weight();
        RVec<float> eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetTvsQCD_score, RVec<int> jetCat);
};

PNetTopSF_weight::PNetTopSF_weight(std::string year, std::string effpath, float wp) : _year(year), _wp(wp) {
    _effroot = TFile::Open(effpath.c_str(),"READ");
};

PNetTopSF_weight::~PNetTopSF_weight() {
    _effroot->Close();
};

int PNetTopSF_weight::GetPtBin(float pt) {
    // pT binning differs for signal (PNet) SFs - handle that here
    int ptBin;
    if      (pt >= 300 && pt < 400) { ptBin = 0; }
    else if (pt >= 400 && pt < 480) { ptBin = 1; }
    else if (pt >= 480 && pt < 600) { ptBin = 2; }
    else if (pt >= 600) { ptBin = 3; }
    else { ptBin = 0; }
    return ptBin;
};

float PNetTopSF_weight::GetSF(float pt, int variation) {
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

float PNetTopSF_weight::GetEff(float pt, float eta, int jetCat) {
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
    delete _effmap;
    return eff;
};

RVec<float> PNetTopSF_weight::eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetTvsQCD_score, RVec<int> jetCat) {
    RVec<float> out(3);
    for (int var : {0,1,2}) {
        float MC_tagged = 1.0, MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;
        float PNetTop_event_weight;
        for (int i=0; i<pt.size(); i++) {
            float SF, eff;
            SF = GetSF(pt[i], var);
            eff = GetEff(pt[i], eta[i], jetCat[i]);
            if (PNetTvsQCD_score[i] > _wp) {
                MC_tagged *= eff;
                data_tagged *= SF*eff;
            }
            else {
                MC_notTagged *= (1.-eff);
                data_notTagged *= (1.-SF*eff);
            }
        }
        if ( (MC_tagged * MC_notTagged) == 0.0) {
            PNetTop_event_weight = 1.0;
        }
        else {
            PNetTop_event_weight = (data_tagged * data_notTagged) / (MC_tagged * MC_notTagged);
        }
        out[var] = PNetTop_event_weight;
    }
    return out;
};
