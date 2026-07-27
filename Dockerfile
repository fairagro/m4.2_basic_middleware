# Use secure Wolfi base image (without Python installed)
FROM cgr.dev/chainguard/wolfi-base@sha256:003627df3c1e1bba0c4116afcddb314aca9594ee2328c7e876a8081a6c988b2e AS builder
# Do not cache the Python bytecode (aka don't create__pycache__ folders)
ENV PYTHONDONTWRITEBYTECODE=1
# Do not buffer stdout/stderr
ENV PYTHONUNBUFFERED=1
# Set the working directory in the container
WORKDIR /middleware
# Install python and needed build tools
RUN apk add --no-cache \
    python-3.12=3.12.13-r10 \
    py3.12-pip=26.1.2-r1 \
    python-3.12-dev=3.12.13-r10 \
    jq=1.8.2-r0 \
    build-base=1-r9
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Copy the requirements.txt file to the container
COPY requirements.txt .
# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt --user

# Actually we would like to use the Wolfi python image for the runtime as it contains even less software (e.g. no shell)
# and thus a smaller attack surface. Unfortunately the Wolfi project only features the current development versions of
# images for free. The older but stable python 3.11 is not available.
FROM cgr.dev/chainguard/wolfi-base@sha256:003627df3c1e1bba0c4116afcddb314aca9594ee2328c7e876a8081a6c988b2e
# Set the working directory in the container
# copy python packages from builder stage
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
COPY middleware/ /middleware/
COPY config.yml /middleware/config.yml
# We also copy the container-structure-test environment. This make it a lot easier to test the resulting container.
COPY test/ /test/
COPY entrypoint.sh /entrypoint.sh
# In in one step, so we do not create layers:
# Install python, git and ssh (the latter two are needed by the middleware)
# Actually install the copied packages
# Create output directory (mountpoint)
# and set permissions of the middleware folder
RUN apk add --no-cache \
        python-3.12=3.12.13-r10 \
        py3.12-setuptools=83.0.0-r0 \
        git=2.55.0-r4 \
        jq=1.8.2-r0 \
        openssh-client=10.4_p1-r1 && \
    chown -R nonroot:nonroot /middleware /test && \
    chmod +x /entrypoint.sh
WORKDIR /
USER nonroot
# Change user context to nonroot
ENTRYPOINT ["/entrypoint.sh"]
# Set the command to run when the container starts
CMD ["python", "-m", "middleware.main", "-c", "/middleware/config.yml"]


