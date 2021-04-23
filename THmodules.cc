#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;

RVec<int> PickDijets(RVec<float> pt, RVec<float> eta, RVec<float> phi, RVec<float> mass) {
    int jet0Idx = -1;
    int jet1Idx = -1;
    for (int ijet = 0; ijet < pt.size(); ijet++) {
        if (jet1Idx == -1) {
            if (pt[ijet] > 350 && std::abs(eta[ijet]) < 2.4 && mass[ijet] > 50) {
                if (jet0Idx == -1) {
                    jet0Idx = ijet;
                } else {
                    if (hardware::DeltaPhi(phi[jet0Idx], phi[ijet]) > M_PI/2) {
                        jet1Idx = ijet;
                        break;
                    }
                }
            }
        }       
    }
    return {jet0Idx,jet1Idx};
}

std::vector<int> PickTop(RVec<float> mass, RVec<float> tagScore, RVec<int> idxs) {
    if (idxs.size()>2) {
        std::cout << "PickTop -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    std::vector<int> out(2);

    int idx0 = idxs[0];
    int idx1 = idxs[1];
    bool isTop0 = (mass[idx0] > 105) && (mass[idx0] < 210) && (tagScore[idx0] > 0.632);
    bool isTop1 = (mass[idx1] > 105) && (mass[idx1] < 210) && (tagScore[idx1] > 0.632);

    if (isTop0 && isTop1) {
        if (tagScore[idx0] > tagScore[idx1]) {
            out[0] = idx0;
            out[1] = idx1;
        } else {
            out[0] = idx1;
            out[1] = idx0;
        }
    } else if (isTop0) {
        out[0] = idx0;
        out[1] = idx1;
    } else if (isTop1) {
        out[0] = idx1;
        out[1] = idx0;
    } else {
        out[0] = -1;
        out[1] = -1;
    }
    return out;
}