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
# We need python and git in the runtime image and ensure the middleware folder belongs to nonroot
RUN apk add --no-cache python-${python_version} py${python_version}-setuptools git openssh-client
# Copy the application from host
COPY middleware/ /middleware/
# copy python packages from builder stage
COPY --from=builder /home/nonroot/.local /home/nonroot/.local
RUN mkdir /middleware/output && \
    chown -R nonroot:nonroot /middleware/
# Set the user to nonroot. It's defined in the Wolfi base image with the user id 65532
USER nonroot
VOLUME /middleware/output
# # copy python "binaries"
# COPY --from=builder /usr/local/bin /usr/local/bin
# Set the command to run when the container starts
CMD [ "python", "main.py", "-c", "config.yml" ]


