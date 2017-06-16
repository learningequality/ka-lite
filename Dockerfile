FROM ubuntu:xenial

# install latest python and nodejs
RUN apt-get -y update --fix-missing
RUN apt-get install -y software-properties-common curl
RUN add-apt-repository ppa:voronov84/andreyv
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y update --fix-missing
RUN apt-get install -y python2.7 python-pip git nodejs  gettext python-sphinx

COPY . /kalite
VOLUME /kalitedist/

# for mounting the whl files into other docker containers
RUN pip install virtualenv && virtualenv /kalite/kalite_env  --python=python2.7
RUN /kalite/kalite_env/bin/pip install -r /kalite/requirements_dev.txt && /kalite/kalite_env/bin/pip install -r /kalite/requirements_sphinx.txt

# Lets override the PATH to add the path of our virtualenv python binaries first so it's python executes instead of
# the system python.
ENV PATH=/kalite/kalite_env/bin:$PATH
ENV KALITE_PYTHON=/kalite/kalite_env/bin/python

CMD cd /kalite && make dist && cp /kalite/dist/* /kalitedist/