#include "ROOT/RVec.hxx"

using namespace ROOT::VecOps;

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