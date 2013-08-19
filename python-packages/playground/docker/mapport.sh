echo "Mapping port. Incoming traffic on port $1 will now be directed to port $2."
sudo iptables -t nat -A PREROUTING -p tcp --dport $1 -j REDIRECT --to $2
