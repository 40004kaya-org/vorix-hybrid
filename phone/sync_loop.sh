#!/data/data/com.termux/files/usr/bin/bash
while true; do
    bash ~/vorix-hybrid/sync_to_github.sh >> ~/vorix-hybrid/sync.log 2>&1
    sleep 60
done
