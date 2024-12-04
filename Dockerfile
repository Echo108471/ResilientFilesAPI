FROM ubuntu:20.04

# Prevent prompts and dialogues during package installation
ENV DEBIAN_FRONTEND=noninteractive 

# Setup the deadsnakes PPA and install essential packages
RUN apt-get update && apt-get install -y \
    software-properties-common \
    apt-transport-https \
    curl \
    gnupg \
    git \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update

# Install required packages, including Python 3.10 and dependencies
RUN apt-get install -y \
    protobuf-compiler \
    rapidjson-dev \
    clang-format \
    build-essential \
    openjdk-11-jdk \
    zip unzip \
    python3.10 \
    python3.10-dev \
    python3-venv \
    python3-dev \
    python3-pip \
    python3-distutils



# Set Python 3.10 as the default python3 version
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    python3 --version

# Install pip3 using the get-pip.py script
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# Cleanup apt cache
RUN rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your project files to the container
COPY . /app

RUN pip install --upgrade setuptools

RUN pip install -r requirements.txt

# Set default environment variable for Render's PORT
ENV PORT 8000

# Expose the port Render expects (if different, adjust in Render dashboard)
EXPOSE 8000  
 
# Start the application using uvicorn
CMD ["uvicorn", "main_server:app", "--host", "0.0.0.0", "--port", "8000"]
