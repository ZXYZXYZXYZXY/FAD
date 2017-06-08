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
    r1 = prob2(L, k)
    r2 = 0
    for l in range(2, L-1):
        r2 += prob1(L, l, k)
    return (r1, r2/(L-3)) if (L-3 != 0) else (r1, 0)

if __name__ == '__main__':
    for i in range(3,129):
        prob_with_k_probe = []
        max_prob_pair = (0, 0, 0)
        for j in range(0, i-1):
            pair = prob_metric(i, j)
            prob_with_k_probe.append(pair)
            if(pair[0] + pair[1] > max_prob_pair[0] + max_prob_pair[1]):
                max_prob_pair = (pair[0], pair[1], j)
        print('%4d \t %4d \t %4f \t %4f \t %4f' % (i, max_prob_pair[2], (max_prob_pair[0] + max_prob_pair[1])/2, max_prob_pair[0], max_prob_pair[1]))
        
        
