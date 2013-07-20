for i in `sudo iptables -t nat -L PREROUTING --line-numbers | grep -E "(dpt:|ports )$1\b" | awk '{print $1}' | sort -r`; do
    echo Unmapping "$i"
    sudo iptables -t nat -D PREROUTING $i
done

