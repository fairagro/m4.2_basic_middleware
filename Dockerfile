# Use secure Wolfi base image (without Python installed)
FROM cgr.dev/chainguard/wolfi-base@sha256:e1d402d624011d0f4439bfb0d46a3ddc692465103c7234a326e0194953c3cfe0 AS builder
# Do not cache the Python bytecode (aka don't create__pycache__ folders)
ENV PYTHONDONTWRITEBYTECODE=1
# Do not buffer stdout/stderr
ENV PYTHONUNBUFFERED=1
# Set the working directory in the container
WORKDIR /middleware
# Install python and needed build tools
RUN apk add --no-cache \
    python-3.12=3.12.10-r0 \
    py3.12-pip=25.1-r0 \
    python-3.12-dev=3.12.10-r0 \
    jq=1.8.1-r2 \
    build-base=1-r8
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Copy the requirements.txt file to the container
COPY requirements.txt .
# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt --user

# Actually we would like to use the Wolfi python image for the runtime as it contains even less software (e.g. no shell)
# and thus a smaller attack surface. Unfortunately the Wolfi project only features the current development versions of
# images for free. The older but stable python 3.11 is not available.
FROM cgr.dev/chainguard/wolfi-base@sha256:e1d402d624011d0f4439bfb0d46a3ddc692465103c7234a326e0194953c3cfe0
# Set the working directory in the container
# copy python packages from builder stage
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
# In in one step, so we do not create layers:
# Install python, git and ssh (the latter two are needed by the middleware)
# Actually install the copied packages
# Create output directory (mountpoint)
# and set permissions of the middleware folder
RUN apk add --no-cache \
        python-3.12=3.12.10-r0 \
        py3.12-setuptools=80.0.0-r0 \
        git=2.49.0-r1 \
        jq=1.8.1-r2 \
        openssh-client=10.0_p1-r0 && \
    mkdir -p /middleware/output && \
    chown nonroot:nonroot /middleware/output
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
# Copy the application from host
COPY middleware/ /middleware/
COPY config.yml /middleware/config.yml
# We also copy the container-structure-test environment. This make it a lot easier to test the resulting container.
COPY test/container-structure-test /middleware/test/container-structure-test
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Change user context to nonroot
USER nonroot
ENTRYPOINT ["/entrypoint.sh"]
# Set the command to run when the container starts
CMD ["python", "-m", "middleware.main", "-c", "/middleware/config.yml"]


