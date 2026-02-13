import sys
import os
import site

# Add user site-packages to path
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

import httpx

# Test annotations endpoint
try:
    r = httpx.get('http://localhost:8001/api/annotations/RELIANCE', timeout=5.0)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Error: {e}')
