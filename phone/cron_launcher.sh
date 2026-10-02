#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export HOME=/data/data/com.termux/files/home

# اگه keepalive در حال اجراست، کاری نکن
if pgrep -f keepalive.sh > /dev/null; then
    exit 0
fi

cd $HOME/vorix-hybrid/phone

# setsid = کاملاً جدا از cron
setsid ./keepalive.sh </dev/null >/dev/null 2>&1 &
