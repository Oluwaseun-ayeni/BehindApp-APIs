FROM kong:2.5.0-alpine

# Switch to root user to install packages
USER root

# Install necessary build tools and dependencies
RUN apk update && \
    apk add --no-cache \
        python3 \
        python3-dev \
        py3-pip \
        libffi-dev \
        gcc \
        musl-dev \
        libressl-dev \
        build-base \
        curl \
        vim\
        postgresql-dev  # Install postgresql-dev for pg_config

# Set the working directory
WORKDIR /app

# Update pip and setuptools to ensure you can install pre-built wheels if available
RUN pip install --no-cache-dir --upgrade pip setuptools

# Create a virtual environment and activate it
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Attempt to install Rust compiler to build cryptography from source if necessary
# Install Rust using rustup
RUN apk add --no-cache curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    source $HOME/.cargo/env

# Ensure the Rust compiler is available in the PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Kong OIDC plugin
RUN luarocks install kong-oidc

# Change ownership of the /app directory to the kong user
RUN chown -R kong:kong /app

# Clean up unnecessary packages and files
RUN apk del curl && \
    rm -rf /var/cache/apk/* /root/.cargo /tmp/* /var/tmp/*

# Switch back to the Kong user for security reasons
USER kong

# Set the command to run Kong or other service
CMD ["kong", "start"]
