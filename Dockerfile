# Use secure Wolfi base image (without Python installed)
FROM cgr.dev/chainguard/wolfi-base@sha256:35c767080978768b86904e6c64845736c3cf05c406299b944dcd24ffe8270df5 AS builder
# Set the version of Python to install
ARG python_version=3.12
# Do not cache the Python bytecode (aka don't create__pycache__ folders)
ENV PYTHONDONTWRITEBYTECODE=1
# Do not buffer stdout/stderr
ENV PYTHONUNBUFFERED=1
# Set the working directory in the container
WORKDIR /middleware
# Install python and needed build tools
RUN apk add --no-cache python-${python_version} py${python_version}-pip python-${python_version}-dev build-base
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Copy the requirements.txt file to the container
COPY requirements.txt .
# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt --user

# Actually we would like to use the Wolfi python image for the runtime as it contains even less software (e.g. no shell)
# and thus a smaller attack surface. Unfortunately the Wolfi project only features the current development versions of
# images for free. The older but stable python 3.11 is not available.
FROM cgr.dev/chainguard/wolfi-base@sha256:35c767080978768b86904e6c64845736c3cf05c406299b944dcd24ffe8270df5
# python_version is out of scope now, so we need to redefine it
ARG python_version=3.12
# Set the working directory in the container
WORKDIR /middleware
# copy python packages from builder stage
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
# In in one step, so we do not create layers:
# Install python, git and ssh (the latter two are needed by the middleware)
# Actually install the copied packages
# Create output directory (mountpoint)
# and set permissions of the middleware folder
RUN apk add --no-cache python-${python_version} py${python_version}-setuptools git openssh-client && \
    mkdir /middleware/output && \
    chown nonroot:nonroot /middleware/output
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Copy the application from host
COPY middleware/ /middleware/
# We also copy the container-structure-test environment. This make it a lot easier to test the resulting container.
COPY test/container-structure-test /middleware/test/container-structure-test
# Mount a volume for the output
VOLUME /middleware/output
# Set the command to run when the container starts
CMD [ "python", "main.py", "-c", "config.yml" ]


