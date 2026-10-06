import sys, io

for f in ['osint_agent.yy', 'osint_agent_v2.py', 'real_osint_agent.py']:
    c = open(f).read()
    old = "sys.stdout = io.TextIoWrapper(sys.stdout.buffer, errors='replace')"
    new = "sys.stdout = io.TextIOWrapper(sys.__stdout.buffer, errors='replace')"
    if old in c:
        c = c.replace(old, new)
        open(f, 'w').write(c)
        print(f'Fixed: {f}')
    else:
        print(f'Skip: {f}')
print('done')
