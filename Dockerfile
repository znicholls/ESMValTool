FROM continuumio/miniconda3

# install development tools
RUN apt-get update -y && apt-get install -y build-essential

# create directory for downloaded files
RUN mkdir /src
WORKDIR /src

# To be on the safe side, update to the latest conda.
# This should not be needed if the miniconda3 container is up to date.
RUN conda update -y conda

#copy list of dependancies from context (esmvaltool source code repo)
COPY environment.yml /src/environment.yml

#install dependancies in root/base environment of conda
RUN conda env update -f /src/environment.yml --name base

#Copy entire ESMValTool source into the container
#TODO: perhaps we could only install parts
RUN mkdir -p /src/ESMValTool/
COPY . /src/ESMValTool/

WORKDIR /src/ESMValTool

RUN python setup.py test

RUN python setup.py install

ENTRYPOINT ["esmvaltool"]
CMD ["--help"]
