#include<ROOT/RVec.hxx>
#include <TRandom.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>

/*
 * Class for applying ParticleNet scale factors on a jet-by-jet basis. 
 * For use in the T' -> t\phi analysis, with scale factors located at:
 * https://coli.web.cern.ch/coli/.cms/btv/boohft-calib/20220623_bb_TprimeB_useExpr_2016/4_fit/
 * 
 * Method: https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b
 * There are a few things for consideration:
 *  1) You have to run this for each working point, so that jets that were reassigned for the first WP are used for the second.
 *     To do so, create a new column using TIMBER analyzer's Define() method and pass the new column to the updateTag() method.
 *  2) The efficiencies do not always obey e_hp < e_mp < 1, so this has to be accounted for in the equality check functions.
*/

using namespace ROOT::VecOps;

class PNetSFHandler {
  private:
    RVec<float> _wps;     // MP [0.8, 0.98], HP [0.98, 1.0]
    RVec<float> _effs;    // efficiencies will be calculated via TIMBER then fed to constructor
    std::string _year;    // 2016APV, 2016, 2017, 2018
    int _var;             // 0: nominal, 1: up, 2: down, passed to constructor
    TRandom _rand;        // used for random number generation
    int _newTags[3]  = {0,0,0};      // number of jets in each new category [fail][loose][tight]
    int _origTags[3] = {0,0,0};      // original num jets in each category [fail][loose][tight]
    
    // SF[_var][pt]
    // variations are described above, pt cats are [400, 600), [600, 800), [800, +inf) across all years
    // HP (tight) [0.98, 1.0]
    float SF2016APV_T[3][3] = {{1.163,1.206,1.491},{1.437,1.529,2.083},{0.949,0.924,0.909}};
    float SF2016_T[3][3]    = {{1.012,1.247,1.188},{1.180,1.509,1.424},{0.899,0.999,0.960}};
    float SF2017_T[3][3]    = {{0.946,1.027,0.900},{1.075,1.158,1.026},{0.830,0.880,0.752}};
    float SF2018_T[3][3]    = {{1.020,1.013,1.082},{1.146,1.110,1.240},{0.894,0.912,0.961}};
    // MP (loose) [0.8, 0.98]
    float SF2016APV_L[3][3] = {{1.102,1.103,0.645},{1.321,1.355,1.914},{0.918,0.871,0.955}};
    float SF2016_L[3][3]    = {{1.032,1.173,1.145},{1.134,1.382,1.332},{0.932,0.970,0.954}};
    float SF2017_L[3][3]    = {{0.973,1.006,1.059},{1.026,1.064,1.132},{0.904,0.931,0.982}};
    float SF2018_L[3][3]    = {{0.904,0.921,1.087},{0.966,0.969,1.165},{0.824,0.841,0.975}};

  public:
    PNetSFHandler(RVec<float> wps, RVec<float> effs, std::string year, int var);  // default: wps={0.8,0.98}, effs={effl,effT}, var=0/1/2
    ~PNetSFHandler(){};
    int getWPcat(float taggerVal);                                    // determine WP category: 0: fail, 1: loose, 2: tight
    float getSF(float pt, float taggerVal);                           // gets the proper SF based on jet's pt and score as well as internal variables _year, _var
    RVec<int> updateTag(RVec<int> jetCats, RVec<float> pt, RVec<float> taggerVals);   // determines the jet's new tagger category 
    RVec<int> createTag(RVec<float> taggerVals);                      // create vector of tagger categories based on jets' original tagger value.

    int test(float taggerVal);

    //int bothLessThanOne(int jetCat, float sf_l, float sf_t);        // both HP, MP SFs < 1
    //int bothGreaterThanOne(int jetCat, float sf_l, float sf_t);     // both HP, MP SFs > 1
    //int LLowerTGreaterThanOne(int jetCat, float sf_l, float sf_t);  // MP SF < 1, HP SF > 1
    //int LGreaterTLowerThanOne(int jetCat, float sf_l, float sf_t);  // MP SF > 1, HP SF < 1
};

PNetSFHandler::PNetSFHandler(RVec<float> wps, RVec<float> effs, std::string year, int var) {
  _wps = wps;
  _effs = effs;
  _year = year;
  _var = var;
  // unique but repeatable random numbers. For repeated calls in the same event, random #s from Rndm() will be identical
  _rand = TRandom(1234);
};

int PNetSFHandler::test(float taggerVal) {
    if ((taggerVal > _wps[0]) && (taggerVal < _wps[1])) return 1;
    if (taggerVal > _wps[1]) return 2;
    if (taggerVal < _wps[0]) return 0;
}

int PNetSFHandler::getWPcat(float taggerVal) {
  // determine the WP category we're in, 0:fail, 1:loose, 2:tight
  int wpCat;
  if ((taggerVal > _wps[0]) && (taggerVal < _wps[1])) { // loose
    wpCat = 1;
  }
  else if (taggerVal > _wps[1]) { // tight
    wpCat = 2;
  }
  else {  // fail
    wpCat = 0;
  }
  return wpCat;
}

float PNetSFHandler::getSF(float pt, float taggerVal) {
  /* getthe scale factor from the jet's year, score, and pt */
  float SF;
  int ptCat;
  int wpCat = getWPcat(taggerVal);
  // get the pT category
  if ((pt >= 400) && (pt < 600)) {
    ptCat = 0;
  }
  else if ((pt >= 600) && (pt < 800)) {
    ptCat = 1;
  }
  else if (pt > 800) {
    ptCat = 2;
  }
  else {
    // jet is outside of the pt range used in SF derivation, return no change
    return 1.0;
  }
  // get the SF
  switch (wpCat) {
    case 0:   // if jet is originally in fail, pass SF of 1.0 (no change)
      SF = 1.0;
    case 1:   // jet is in MP (loose)
      if (_year=="2016APV") { SF = SF2016APV_L[_var][ptCat]; }
      else if (_year=="2016") { SF = SF2016_L[_var][ptCat]; }
      else if (_year=="2017") { SF = SF2017_L[_var][ptCat]; }
      else { SF = SF2018_L[_var][ptCat]; }
    case 2:   // jet is in HP (tight)
      if (_year=="2016APV") { SF = SF2016APV_T[_var][ptCat]; }
      else if (_year=="2016") { SF = SF2016_T[_var][ptCat]; }
      else if (_year=="2017") { SF = SF2017_T[_var][ptCat]; }
      else { SF = SF2018_T[_var][ptCat]; }
  }
  return SF;
}

RVec<int> PNetSFHandler::createTag(RVec<float> taggerVals) {
  /* Creates tagger categories for phi candidate jets.
   * This MUST be called in TIMBER before running the rest of the script, as it places all jets into their respective categories for later use in updateTag()
   * example calling from TIMBER (after compiling class): analyzer.Define("ScaledPnetH","PNetSFHandler.createTag(particleNetMD_HbbvsQCD);")
   * cat (int): 0-fail, 1-MP(loose), 2-HP(tight)
  */
  //std::cout << "in vec size: " << taggerVals.size() << "\n"; 
  //printf("Creating tag categories - 0: Fail, 1: Loose, 2: Tight\n");
  RVec<int> jetCats(taggerVals.size());
  for (size_t ijet=0; ijet<taggerVals.size(); ijet++) {   // loop over all jets
    int cat;
    float taggerVal = taggerVals[ijet];
    if ((taggerVal > _wps[0]) && (taggerVal < _wps[1])) {   // 0.8 < tag < 0.98
      _origTags[1]++;
      jetCats[ijet] = 1;
    }
    else if ((taggerVal > _wps[1])) {   // tag > 0.98
      _origTags[2]++;
      jetCats[ijet] = 2;
    }
    else {    // tag < 0.8
      _origTags[0]++;
      jetCats[ijet] = 0;
    }
  }
  //printf("Finished creating tag categories. Initial values before btag reassignment:\n\tFail: %i\n\tLoose: %i\n\tTight: %i\n",_origTags[0],_origTags[1],_origTags[2]);
  return jetCats;
};

RVec<int> PNetSFHandler::updateTag(RVec<int> jetCats, RVec<float> pt, RVec<float> taggerVals) {
  /* https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b 
   * params:
   *    jetCats = vector of ints representing the category into which each jet has been placed (0:fail, 1:loose, 2:tight)
   *        - should be passed the RVec created by createTag()
   *    pt = vector of floats holding each jet's pt
   * returns:
   *    cats = new vector of ints representing the jet categories after checking the four SF conditions
  */
  //printf("Updating tag categories - 0: Fail, 1: Loose, 2: Tight\n");
  RVec<int> cats(jetCats.size());
  float eff_L = _effs[0];
  float eff_T = _effs[1];
  for (size_t ijet=0; ijet<pt.size(); ijet++) {
    // get the SF for loose and tight using the jet's pt, tagger value. The getSF() function uses the internal year value and calculates the tagger WP
    // pt, taggerVals, and jetCats should be same length, so ijets should work for indexing
    float SF_L = getSF(pt[ijet], taggerVals[ijet]);
    float SF_T = getSF(pt[ijet], taggerVals[ijet]);
    int newCat = jetCats[ijet];   // grab the original tag category

    // generate the random number for the event 
    double rn = _rand.Rndm();
    //printf("\trn: %f",rn);

    /* BROKEN - results in very incorrect retag values across nom/up/down
    // check the four cases and modify the new category appropriately
    if ((SF_L < 1) && (SF_T < 1)) {
      if ( (newCat==2) && (rn < (1-SF_T)) ) newCat--;                         // demote from tight (2) to loose (1)
      if ( (newCat==1) && (rn < (1-SF_L)/(1-(eff_T/eff_L)*SF_T)) ) newCat--;  // demote from loose (1) to untag (0)
    }
    else if ((SF_L > 1) && (SF_T > 1)) {
      if ( (newCat==0) && (rn < (SF_L-1)/((1./eff_L)-1)) ) newCat++;          // promote from untag (0) to loose (1)
      if ( (newCat==1) && (rn < (SF_T-1)/((eff_L/eff_T)*SF_T-1)) ) newCat++;  // promote from loose (1) to tight (2)
    }
    else if ((SF_L < 1) && (SF_T > 1)) {
      if ( (newCat==0) && (rn < (eff_T*(SF_T-1))/(1-(eff_T+eff_L)) ) ) newCat++;   // promote from loose (1) to tight (2)
      if ( (newCat==1) && (rn < (1-SF_T)) ) newCat--;                              // demote from loose (1) to untag(0)
    }
    else if ((SF_L > 1) && (SF_T < 1)) {
      if ( (newCat==2) && (rn < (1-SF_T)) ) newCat--;                              // demote from tight (2) to loose (1)
      if ( (newCat==0) && (rn < (eff_L*(SF_L-1))/(1-(eff_T+eff_L))) ) newCat++;    // promote from untag (0) to loose (1)
    }
    */

    if ((SF_L < 1) && (SF_T < 1)) {
      if ( (newCat==2) && (rn < (1.-SF_T)) ) newCat--;                         // demote from tight (2) to loose (1)
      if ( (newCat==1) && (rn < (1.-SF_L)) ) newCat--;                         // demote from loose (1) to untag (0)
    }
    else if ((SF_L > 1) && (SF_T > 1)) {
      if (newCat==0) {
        if (rn < (eff_T*(SF_T-1.))/(1.-eff_L+eff_T)) newCat=2;                 // promote from untag (0)  to tight (2)
        if (rn < (eff_L*(SF_L-1.))/(1.-eff_L-eff_T)*(1.-(eff_T*(SF_T-1.))/(1.-eff_L+eff_T)) ) newCat++;   // promote from untag (0) to loose (1)
      }
    }
    else if ((SF_L < 1) && (SF_T > 1)) {
      if ( (newCat==0) && (rn < (eff_T*(SF_T-1.))/(1.-(eff_L+eff_T)) ) ) newCat=2;  // promote from untag (0) to tight (2)
      if ( (newCat==1) && (rn < 1.-SF_L) ) newCat--;                                // demote from loose (1) to untag (0)    
    }
    else if ((SF_L > 1) && (SF_T < 1)) {
      if ( (newCat==2) && (rn <  1.-SF_T) ) newCat=0;                               // demote from tight (2) to untag (0)
      if ( (newCat==0) && (rn < (eff_L*(SF_L-1.))/(1.-(eff_L+eff_T)) ) ) newCat++;  // promote from untag (0) to loose (1)
    }

    // append new category value to RVec
    cats[ijet] = newCat;
    // update the new tag category array
    _newTags[newCat]++;
  }
  // values in _newTags array MUST be updated during the 4 above subroutines based on their outcome
  //printf("Finished updating tag categories. New values after btag reassignment:\n\tFail: %i\n\tLoose: %i\n\tTight: %i\n",_newTags[0],_newTags[1],_newTags[2]);
  return cats;
};
