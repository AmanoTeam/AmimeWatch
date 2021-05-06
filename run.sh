# Update package repositories
apt-get update -y

# Install docker
apt-get install -y --no-install-recommends docker.io

# Build
docker build -t amime .

# RUN
docker run -d -it --name amime -v database:/app/database amime