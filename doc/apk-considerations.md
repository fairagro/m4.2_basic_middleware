# Thinking about using Wolfi base images and apk packages #

When using Wolfi for building secure docker images, the preferred way is not to use Dockerfile, but the package manager apko. This requires to create an apk package for the middleware. This is turn requires that all dependencies of the middleware also need to be available in terms of Wolfi apk packages. So this is an overview which apk packages are available.

Having a look at the list below, it's clear that most packages are missing. Trying to build these package using the tool `melange` is actually quite easy. It just requires a JSON file to be creates that defines package metadata (name, version, dependencies, licence ...) and download location -- at least if it's a pure python package. In case it's another languag -- like C -- the package needs to be build which can be quote complex. This is the case for `grpcio`. Having a look at the Alpine `py3-grpcio` package reveals how to build it, but this approach currently does not work -- probably because of version mismatches of involved libraries.

```text
N   aiofiles==23.2.1
Y   aiohttp==3.9.0
    ├── aiosignal [required: >=1.1.2, installed: 1.3.1]
    │   └── frozenlist [required: >=1.1.0, installed: 1.4.0]
    ├── attrs [required: >=17.3.0, installed: 23.1.0]
    ├── frozenlist [required: >=1.1.1, installed: 1.4.0]
    ├── multidict [required: >=4.5,<7.0, installed: 6.0.4]
    └── yarl [required: >=1.0,<2.0, installed: 1.9.3]
        ├── idna [required: >=2.0, installed: 3.4]
        └── multidict [required: >=4.0, installed: 6.0.4]
N   aioitertools==0.11.0
N   asyncstdlib==3.10.9
N   chardet==5.2.0
N   extruct==0.16.0
N   ├── html-text [required: >=0.5.1, installed: 0.5.2]
Y   │   └── lxml [required: Any, installed: 4.9.3]
N   ├── jstyleson [required: Any, installed: 0.0.2]
Y   ├── lxml [required: Any, installed: 4.9.3]
N   ├── mf2py [required: Any, installed: 1.1.3]
Y   │   ├── beautifulsoup4 [required: >=4.6.0, installed: 4.12.2]
    │   │   └── soupsieve [required: >1.2, installed: 2.5]
Y   │   ├── html5lib [required: >=1.0.1, installed: 1.1]
    │   │   ├── six [required: >=1.9, installed: 1.16.0]
    │   │   └── webencodings [required: Any, installed: 0.5.1]
    │   └── requests [required: >=2.18.4, installed: 2.31.0]
    │       ├── certifi [required: >=2017.4.17, installed: 2023.11.17]
    │       ├── charset-normalizer [required: >=2,<4, installed: 3.3.2]
    │       ├── idna [required: >=2.5,<4, installed: 3.4]
    │       └── urllib3 [required: >=1.21.1,<3, installed: 2.1.0]
N   ├── pyRdfa3 [required: Any, installed: 3.5.3]
Y   │   ├── html5lib [required: Any, installed: 1.1]
    │   │   ├── six [required: >=1.9, installed: 1.16.0]
    │   │   └── webencodings [required: Any, installed: 0.5.1]
Y   │   └── rdflib [required: Any, installed: 7.0.0]
    │       ├── isodate [required: >=0.6.0,<0.7.0, installed: 0.6.1]
    │       │   └── six [required: Any, installed: 1.16.0]
    │       └── pyparsing [required: >=2.1.0,<4, installed: 3.1.1]
Y   ├── rdflib [required: >=6.0.0, installed: 7.0.0]
    │   ├── isodate [required: >=0.6.0,<0.7.0, installed: 0.6.1]
    │   │   └── six [required: Any, installed: 1.16.0]
    │   └── pyparsing [required: >=2.1.0,<4, installed: 3.1.1]
Y   ├── six [required: Any, installed: 1.16.0]
N   └── w3lib [required: Any, installed: 2.1.2]
N   GitPython==3.1.40
N   └── gitdb [required: >=4.0.1,<5, installed: 4.0.11]
N       └── smmap [required: >=3.0.1,<6, installed: 5.0.1]
N   opentelemetry-exporter-otlp-proto-grpc==1.21.0
N   ├── backoff [required: >=1.10.0,<3.0.0, installed: 2.2.1]
N   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   ├── googleapis-common-protos [required: ~=1.52, installed: 1.61.0]
    │   └── protobuf [required: >=3.19.5,<5.0.0.dev0,!=4.21.5,!=4.21.4,!=4.21.3,!=4.21.2,!=4.21.1,!=3.20.1,!=3.20.0, installed: 4.25.1]
N   ├── grpcio [required: >=1.0.0,<2.0.0, installed: 1.59.3]
N   ├── opentelemetry-api [required: ~=1.15, installed: 1.21.0]
N   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │       └── zipp [required: >=0.5, installed: 3.17.0]
N   ├── opentelemetry-exporter-otlp-proto-common [required: ==1.21.0, installed: 1.21.0]
N   │   ├── backoff [required: >=1.10.0,<3.0.0, installed: 2.2.1]
N   │   └── opentelemetry-proto [required: ==1.21.0, installed: 1.21.0]
Y   │       └── protobuf [required: >=3.19,<5.0, installed: 4.25.1]
N   ├── opentelemetry-proto [required: ==1.21.0, installed: 1.21.0]
Y   │   └── protobuf [required: >=3.19,<5.0, installed: 4.25.1]
N   └── opentelemetry-sdk [required: ~=1.21.0, installed: 1.21.0]
N       ├── opentelemetry-api [required: ==1.21.0, installed: 1.21.0]
N       │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y       │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y       │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
        │       └── zipp [required: >=0.5, installed: 3.17.0]
N       ├── opentelemetry-semantic-conventions [required: ==0.42b0, installed: 0.42b0]
Y       └── typing-extensions [required: >=3.7.4, installed: 4.8.0]
N   opentelemetry-instrumentation-aiohttp-client==0.42b0
N   ├── opentelemetry-api [required: ~=1.12, installed: 1.21.0]
N   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │       └── zipp [required: >=0.5, installed: 3.17.0]
N   ├── opentelemetry-instrumentation [required: ==0.42b0, installed: 0.42b0]
N   │   ├── opentelemetry-api [required: ~=1.4, installed: 1.21.0]
N   │   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │   │       └── zipp [required: >=0.5, installed: 3.17.0]
N   │   ├── setuptools [required: >=16.0, installed: 69.0.2]
Y   │   └── wrapt [required: >=1.0.0,<2.0.0, installed: 1.16.0]
N   ├── opentelemetry-semantic-conventions [required: ==0.42b0, installed: 0.42b0]
N   ├── opentelemetry-util-http [required: ==0.42b0, installed: 0.42b0]
Y   └── wrapt [required: >=1.0.0,<2.0.0, installed: 1.16.0]
N   opentelemetry-instrumentation-requests==0.42b0
N   ├── opentelemetry-api [required: ~=1.12, installed: 1.21.0]
N   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │       └── zipp [required: >=0.5, installed: 3.17.0]
N   ├── opentelemetry-instrumentation [required: ==0.42b0, installed: 0.42b0]
N   │   ├── opentelemetry-api [required: ~=1.4, installed: 1.21.0]
N   │   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
N   │   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │   │       └── zipp [required: >=0.5, installed: 3.17.0]
N   │   ├── setuptools [required: >=16.0, installed: 69.0.2]
Y   │   └── wrapt [required: >=1.0.0,<2.0.0, installed: 1.16.0]
N   ├── opentelemetry-semantic-conventions [required: ==0.42b0, installed: 0.42b0]
N   └── opentelemetry-util-http [required: ==0.42b0, installed: 0.42b0]
N   opentelemetry-instrumentation-urllib==0.42b0
N   ├── opentelemetry-api [required: ~=1.12, installed: 1.21.0]
N   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
Y   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │       └── zipp [required: >=0.5, installed: 3.17.0]
N   ├── opentelemetry-instrumentation [required: ==0.42b0, installed: 0.42b0]
N   │   ├── opentelemetry-api [required: ~=1.4, installed: 1.21.0]
N   │   │   ├── Deprecated [required: >=1.2.6, installed: 1.2.14]
N   │   │   │   └── wrapt [required: >=1.10,<2, installed: 1.16.0]
Y   │   │   └── importlib-metadata [required: >=6.0,<7.0, installed: 6.8.0]
    │   │       └── zipp [required: >=0.5, installed: 3.17.0]
N   │   ├── setuptools [required: >=16.0, installed: 69.0.2]
Y   │   └── wrapt [required: >=1.0.0,<2.0.0, installed: 1.16.0]
N   ├── opentelemetry-semantic-conventions [required: ==0.42b0, installed: 0.42b0]
N   └── opentelemetry-util-http [required: ==0.42b0, installed: 0.42b0]
Y   pytz==2023.3.post1
Y   PyYAML==6.0.1
Y   wheel==0.42.0
```
