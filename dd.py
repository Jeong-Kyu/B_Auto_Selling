d = []
jm_count = 3
for k in range(jm_count): d.append(0)

print(d)
d=[1,2,3]

for u in range(1,jm_count+1):
    print(u)
    d[jm_count-u] = d[jm_count-u-1]
d[0] = 3

print(d)