#!/bin/bash

# EC2 Setup Script for ANPR Backend
# Run this script on a fresh EC2 instance (Ubuntu)

echo "=========================================="
echo "Starting EC2 Setup for ANPR Backend"
echo "=========================================="

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group (no need sudo)
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose standalone (optional, for docker-compose command)
echo "📦 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/anpr-backend
cd ~/anpr-backend

# Create necessary directories
mkdir -p crop model

echo ""
echo "=========================================="
echo "✅ Setup completed successfully!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You need to logout and login again for docker group to take effect"
echo "   Run: exit"
echo "   Then SSH again"
echo ""
echo "📝 Next steps:"
echo "1. Logout and login again (or run: newgrp docker)"
echo "2. Verify Docker: docker --version"
echo "3. Verify Docker Compose: docker-compose --version"
echo "4. The GitHub Actions will automatically deploy to ~/anpr-backend"
echo ""
echo "🔒 Don't forget to:"
echo "   - Configure Security Groups (ports 22, 80, 443)"
echo "   - Update GitHub Secrets with EC2 info"
echo ""
