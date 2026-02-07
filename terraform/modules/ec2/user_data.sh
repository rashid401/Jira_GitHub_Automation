#!/bin/bash
set -eux

# Update OS
yum update -y

# Install Docker
amazon-linux-extras install docker -y

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Allow ec2-user to run docker
usermod -aG docker ec2-user

# Install docker compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Verify installations
docker --version
docker compose version
