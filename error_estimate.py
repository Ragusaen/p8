from mpmath import *


mp.dps = 25

def error_estimate(n: int, k: int, p_f: float = 0.001):
    sum = mpf('0')
    p_f = mpf(p_f)
    for i in range(k + 1, n + 1):
        sum += binomial(n, i) * power(p_f, i) * power(1 - p_f, n - i)

    return sum



print(error_estimate(100, 3))