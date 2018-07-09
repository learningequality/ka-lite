FROM ubuntu:xenial

# install latest python and nodejs
RUN apt-get -y update && \
  apt-get install -y software-properties-common curl && \
  curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
  apt-get -y update && apt-get install -y python2.7 python-pip git nodejs gettext wget

COPY . /kalite
VOLUME /kalitedist/

# Use virtualenv's pip
ENV PIP=/kalite/kalite_env/bin/pip

# for mounting the whl files into other docker containers
RUN pip install virtualenv && virtualenv /kalite/kalite_env  --python=python2.7

RUN $PIP install -r /kalite/requirements_dev.txt \
	&& $PIP install -r /kalite/requirements_sphinx.txt \
	&& $PIP install -e /kalite/. \
	&& $PIP install pex

# Override the PATH to add the path of our virtualenv python binaries first so it's python executes instead of
# the system python.
ENV PATH=/kalite/kalite_env/bin:$PATH
ENV KALITE_PYTHON=/kalite/kalite_env/bin/python

CMD cd /kalite && make dist pex && cp /kalite/dist/* /kalitedist/
