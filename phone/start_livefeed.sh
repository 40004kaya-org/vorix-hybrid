#!/data/data/com.termux/files/usr/bin/bash
cd ~/vorix-hybrid/phone
exec python layer_livefeed.py >> ~/vorix-hybrid/phone/livefeed.out 2>&1
