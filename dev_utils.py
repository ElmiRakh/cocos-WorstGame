from constants import initials
from itertools import product,permutations
import numpy as np
from math import sqrt
from pprint import pprint

def distance(pair):
    x1,y1 = pair[0]
    x2,y2 = pair[1]
    return sqrt((x2-x1)**2 + (y2-y1)**2)//100

def calc_distance_matrix():
	dists = list(product(sorted(list(initials.values())),repeat=2))
	voc = {y:x.rstrip('.png') for x,y in initials.items()}
	voc2 = {y:x for x,y in enumerate(sorted(list(voc.values())))}

	dist_dict = {}
	cost_matrix = np.zeros((7,7))

	for d in dists:
	    key = (voc[d[0]],voc[d[1]])
	    val = distance(d)
	    dist_dict[key] = (val)

	    idx = voc2[key[0]]
	    idy = voc2[key[1]]
	    cost_matrix[idx,idy] = val
	return dist_dict,cost_matrix

if __name__ == '__main__':
	dist_dict,cost_matrix = calc_distance_matrix()
	pprint(dist_dict)