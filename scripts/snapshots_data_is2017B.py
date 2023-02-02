#############################################################
# script to determine the fraction of the total data that 
# belongs to 2017B in order to undertsand effect of !2017B cut 
# due to trigger efficiency
#############################################################

from TIMBER.Analyzer import analyzer 
import ROOT

a = analyzer('data_is2017B.txt')

before = a.DataFrame.Count()

a.Cut('is2017B_cut','is2017B == 0')

after = a.DataFrame.Count()

before = before.GetValue()
after = after.GetValue()

print('Number before: {}'.format(before))
print('Number after: {}'.format(after))

print('after/before = {}/{} = {}'.format(after,before,float(after)/float(before)))
