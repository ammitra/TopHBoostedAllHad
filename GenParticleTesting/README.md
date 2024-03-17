# GenParticleTesting

This contains studies on generator-level checks of the top-merging in the ttbar MC

* `GenParticleChecker.py`: class used to create a tree-like structure of all the generator-level particles in an event
* `ttbar_gen_draw.py`: script to draw the tree of all top decays in an event
* `ttbar_merge_check.py`: Lucas' old code, not useful here but contains some insight as to how to use the class
* `check_top_merging.py`: main analysis script, used to determine the fraction of top-merged, W-merged, and unmerged top quarks in the event. 

# Usage
The `graphviz` package is installed in CMSSW, but some tweaks had to be made. Lucas' generator particle code requires [NanoAOD-tools](https://github.com/cms-nanoAOD/nanoAOD-tools) for the event loop, so it's included here as a submodule. The instructions are linked, but in order to access it in the `timber-env` environment, use the standalone checkout instructions and then remember to `source standalone/env_standalone.sh` before using.
