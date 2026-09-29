# Docker installation
# https://docs.docker.com/engine/install/centos/#install-using-the-repository

# Should follow the below
# https://docs.rockylinux.org/10/gemstones/containers/docker/

sudo dnf -y install dnf-plugins-core

sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker

sudo docker run hello-world