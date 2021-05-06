# Set the OS image
FROM python:3.10.0b1-slim-buster

# Set some info
ENV PIP_NO_CACHE_DIR 1
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Update package repositories
RUN apt-get update -y

# Install some essentials packages
RUN apt-get install -y --no-install-recommends \
    build-essential \
    coreutils \
    curl \
    ffmpeg \
    git \
    g++ \
    libuv1 \
    libuv1-dev \
    neofetch

# Copy the bot
COPY . /app

# Set the workdir
WORKDIR /app

# Set the volume
VOLUME ["/app/database"]

# Install requirements
RUN pip install -U setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Set the bot on PATH environment
ENV PATH="/app/:$PATH"

# RUN
CMD ["python3", "-m", "amime"]