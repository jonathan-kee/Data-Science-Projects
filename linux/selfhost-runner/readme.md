# Vagrant After Setup & Provisioning 
1) cd linux/selfhost-runner
2) vagrant up --provider vmware_desktop
^
GUI Login:
Server1 Login: Vagrant
Password: Vagrant
3) vagrant ssh Server1
4) cd actions-runner
5) sudo chown -R vagrant:vagrant /home/vagrant/actions-runner
6) ./run.sh