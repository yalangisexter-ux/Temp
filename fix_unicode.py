import re
for f in ['osint_agent.py', 'osint_agent_v2.py', 'real_osint_agent.py']:
    c = open(f, encoding='utf-8').read()
    c = c.replace('✓', '[OK]').replace('⚠', '[WARN]').replace('✗', '[ERR]')
    open(f, 'w', encoding='utf-8').write(c)
    print(f'Fixed: {f}')
print('done')
