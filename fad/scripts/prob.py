def prob1(L, l, k):
    """calculate the probability of detecting traffic hijack successfully"""
    tmp = 1.0
    for i in range(2,l+2):
        tmp *= (L-k-i)
        tmp /= (L-i)
    tmp = float(L-k-2)/(L-2) - tmp
    return tmp

def prob2(L, k):
    """calculate the probability of detecting forwarding error successfully"""
    return float(L-k-2)/(L-2)
    
def prob_metric(L, k):
    if isinstance(k, list) == False:
        r = prob2(L, k)
        for l in range(2, L-1):
            r += prob1(L, l, k);
        return r
    else:
        r = []
        for ki in k:
            ri = prob2(L, ki)
            for l in range(2, L-1):
                tmp = prob1(L, l, ki)
                ri += tmp
            ri /= (L-2)
            r.append(ri)
        return r

if __name__ == '__main__':
    for i in range(3,129):
        res = prob_metric(i, range(0, i-1))
        maxi = 0
        for j in range(1, len(res)):
            if res[j] >= res[maxi]:
                maxi = j
        print('%4d %4d %4f'%(i,maxi, res[maxi]))
        
        
