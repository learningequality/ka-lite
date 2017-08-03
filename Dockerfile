FROM ubuntu:xenial

# install latest python and nodejs
RUN apt-get -y update
RUN apt-get install -y software-properties-common curl
RUN add-apt-repository ppa:voronov84/andreyv
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y update && apt-get install -y python2.7 python-pip git nodejs gettext python-sphinx wget

# Install wine and related packages
RUN dpkg --add-architecture i386 
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates sudo software-properties-common
RUN add-apt-repository -y ppa:ubuntu-wine/ppa && apt-get -y update && apt-get install --no-install-recommends --assume-yes wine


COPY . /kalite
VOLUME /kalitedist/

# for mounting the whl files into other docker containers
RUN pip install virtualenv && virtualenv /kalite/kalite_env  --python=python2.7
RUN /kalite/kalite_env/bin/pip install -r /kalite/requirements_dev.txt \
	&& /kalite/kalite_env/bin/pip install -r /kalite/requirements_sphinx.txt \
	&& /kalite/kalite_env/bin/pip install -e /kalite/.

# Override the PATH to add the path of our virtualenv python binaries first so it's python executes instead of
# the system python.
ENV PATH=/kalite/kalite_env/bin:$PATH
ENV KALITE_PYTHON=/kalite/kalite_env/bin/python

# Installer dependencies
RUN cd /kalite/ && git clone https://github.com/learningequality/ka-lite-installers.git
RUN cd /kalite/ka-lite-installers/windows && wget http://pantry.learningequality.org/downloads/ka-lite/0.17/content/contentpacks/en.zip
RUN cp -R /kalite/dist/ka_lite_static-0.17.2.dev1-py2-none-any.whl /kalite/ka-lite-installers/windows

# Build the python packages and the ka-lite windows installer
CMD cd /kalite && make dist \
	&& cd /kalite/ka-lite-installers/windows \
	&& export KALITE_BUILD_VERSION=$(/kalite/kalite_env/bin/kalite --version) \
	&& wine inno-compiler/ISCC.exe installer-source/KaliteSetupScript.iss \
	&& cp /kalite/dist/* /kalitedist/ \
	&& cp /kalite/ka-lite-installers/windows/KALiteSetup-$(/kalite/kalite_env/bin/kalite --version).exe /kalitedist/
