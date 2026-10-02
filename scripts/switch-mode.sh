#!/data/data/com.termux/files/usr/bin/bash
CONFIG=~/vorix-hybrid/config/vorix.config.json
MODE="${1:-status}"

case "$MODE" in
  phone-only)
    python3 -c "import json; c=json.load(open('$CONFIG')); c['mode']='phone-only'; c['features']['cloud_backup']=False; c['features']['cloud_layers']=False; json.dump(c,open('$CONFIG','w'),indent=2); print('mode: phone-only')"
    ;;
  hybrid)
    python3 -c "import json; c=json.load(open('$CONFIG')); c['mode']='hybrid'; c['features']['cloud_backup']=True; c['features']['cloud_layers']=False; json.dump(c,open('$CONFIG','w'),indent=2); print('mode: hybrid')"
    ;;
  cloud)
    python3 -c "import json; c=json.load(open('$CONFIG')); c['mode']='cloud'; c['features']['cloud_backup']=True; c['features']['cloud_layers']=True; c['features']['real_time']=True; json.dump(c,open('$CONFIG','w'),indent=2); print('mode: cloud')"
    ;;
  status)
    python3 -c "import json; c=json.load(open('$CONFIG')); print('Mode:', c['mode']); print('API:', c['endpoints']['api'] or 'not set'); print('Server:', c['server']['host'] or 'not set'); print('Domain:', c['server']['domain'])"
    ;;
  *)
    echo "Usage: switch-mode.sh {phone-only|hybrid|cloud|status}"
    ;;
esac
