# Use secure Wolfi base image (without Python installed)
FROM cgr.dev/chainguard/wolfi-base as builder
# Set the version of Python to install
ARG python_version=3.11
# Install python and needed build tools
RUN apk add python-${python_version} py${python_version}-pip python-${python_version}-dev build-base
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Copy the requirements.txt file to the container
COPY requirements.txt .
# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt --user

# Actually we would like to use the Wolfi python image for the runtime as it contains even less software (e.g. no shell)
# and thus a smaller attack surface. Unfortunately the Wolfi project only features the current development versions of
# images for free. The older but stable python 3.11 is not available.
FROM cgr.dev/chainguard/wolfi-base
# python_version is out of scope now, so we need to redefine it
ARG python_version=3.11
# Set the working directory in the container
WORKDIR /middleware
# We need python, git and ssh in the runtime image
RUN apk add --no-cache python-${python_version} py${python_version}-setuptools git openssh-client
# Copy the application from host
COPY middleware/ /middleware/
# We also copy the container-structure-test environment. This make it a lot easier to test the resulting container.
COPY test/container-structure-test /middleware/test/container-structure-test
# copy python packages from builder stage
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
# Create output directory (mountpoint) and set permissions of the middleware folder
RUN mkdir /middleware/output && \
    chown -R nonroot:nonroot /middleware/
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
# Mount a volume for the output
VOLUME /middleware/output
# Set the command to run when the container starts
CMD [ "python", "main.py", "-c", "config.yml" ]


