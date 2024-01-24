#include <string>
#include "TFile.h"
#include "TEfficiency.h"
#include "TH2.h"
#include <stdio.h>

class EffLoader_2DfittedHist {
    private:
        TFile *file;
        TH2F *hist;
        int binx;
        int globalbin;
        float effval;
        float effup;
        float effdown;
    public:
	~EffLoader_2DfittedHist();
        EffLoader_2DfittedHist(std::string filename, std::string histname);
        std::vector<float> eval_byglobal(int gloablbin);
        std::vector<float> eval_bybin(int binx, int biny, int binz=0);
        std::vector<float> eval(float xval, float yval, float zval=0);
};

EffLoader_2DfittedHist::~EffLoader_2DfittedHist() {
    //std::cout << "TEST\n";
};

EffLoader_2DfittedHist::EffLoader_2DfittedHist(std::string filename, std::string histname) {
    //std::cout << "Opening file " << filename.c_str() << ", histogram " << histname.c_str() << "\n";
    printf("Opening file %s, histogram %s", filename.c_str(), histname.c_str());
    file = TFile::Open(filename.c_str());
    hist = (TH2F*)file->Get(histname.c_str());
};

std::vector<float> EffLoader_2DfittedHist::eval_byglobal(int globalbin) {
    effval = hist->GetBinContent(globalbin);
    effup = effval + hist->GetBinError(globalbin);
    effdown = effval - hist->GetBinError(globalbin);
    return {effval, effup, effdown};
};

std::vector<float> EffLoader_2DfittedHist::eval_bybin(int binx, int biny, int binz) {
    globalbin = hist->FindFixBin(binx, biny, binz);
    return eval_byglobal(globalbin);
};

std::vector<float> EffLoader_2DfittedHist::eval(float xval, float yval, float zval) {
     //std::cout << "(" << xval << "," << yval << ")\n";
     globalbin = hist->FindFixBin(xval, yval, zval);
     return eval_byglobal(globalbin);
};
