import re

with open('latex2/latex/latency_full_median.tex', 'r') as f:
    lines = f.readlines()

    filtered_lines = []

    def fst_or_null(l):
        return None if l is None else l[1]

    filtered_lines.append(lines[0])
    for i in range(1, len(lines) - 1):
        s1 = fst_or_null(re.search(r"""\(\d+, (\d+)\)""", lines[i-1]))
        s2 = fst_or_null(re.search(r"""\(\d+, (\d+)\)""", lines[i]))
        s3 = fst_or_null(re.search(r"""\(\d+, (\d+)\)""", lines[i+1]))
        if s1 != s2 or s3 is None or s2 != s3:
            filtered_lines.append(lines[i])
    filtered_lines.append(lines[-1])

    print(''.join(filtered_lines))
