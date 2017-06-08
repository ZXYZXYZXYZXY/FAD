import matplotlib.pyplot as plt
import collections
import sys
from prob import *

def most_optimal_k(lm):
    Ls = (4, lm+1)
    res = collections.defaultdict(list)
    for L in range(*Ls):
        for l in range(2, L-1):
            x = range(0, L-1)
            yt = prob1(L, l, x)
            y = [v for v in yt if yt > 0]
            max_index = 0
            for index, val in enumerate(y):
                if val > y[max_index]:
                    max_index = index
            res[max_index].append((L, l))
    #         print 'L={},l={} d={} {}'.format(L, l, max(y) - y[1], y)
    # print res
    res2 = {}
    max_key, max_val = (-1, -1)
    for key, vals in res.items():
        res2[key] = len(vals)
        if len(vals) > max_val:
            max_key = key
            max_val = len(vals)
    return max_key

def optimal_deviation(L, index):
    res = [0, 0]
    for l in range(2, L-1):
        x = range(0, L-1)
        yt = prob1(L, l, x)
        y = [v for v in yt if yt > 0]
        deviation = (max(y)-y[index])/max(y)
        res.append(deviation)
    return res
    
    
if __name__ == '__main__':
    Ls = (4,13)
    f, axarr = plt.subplots(Ls[1]-Ls[0], 1, sharex = True)
    if len(sys.argv) != 1:
        for L in range(*Ls):
            ax = axarr[L-Ls[0]]
            ax.set_title('L = {}'.format(L))
            for l in range(2,L-1):
                x = range(0,L-1)
                line, = ax.plot(x,prob1(L,l,x))
                line.set_label('l={}'.format(l))
                ax.legend()
                ax.axis(ymin=-0.1,ymax=1)
        plt.show()
    for i in range(4, 32):
        print '{} {}'.format(i, most_optimal_k(i))
    res = {}
    for L in range(4, 13):
        tmp = optimal_deviation(L,1)
        for l in range(2, 13):
            res[(l,L)] = 0 if len(tmp) <= l else tmp[l]
    for l in range(2,13):
        print l,
        for L in range(4, 13):
            print res[(l,L)],
        print
