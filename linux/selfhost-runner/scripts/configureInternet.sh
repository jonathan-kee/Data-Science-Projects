# Configure Virtual Machine's DNS resolver to reach internet
sudo sh -c 'printf "nameserver 8.8.8.8\nnameserver 1.1.1.1\n" > /etc/resolv.conf'