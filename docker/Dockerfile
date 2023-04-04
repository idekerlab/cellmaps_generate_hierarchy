# Use an official Python runtime as a parent image
FROM continuumio/miniconda3

RUN apt-get --allow-releaseinfo-change update
RUN apt-get install -y build-essential 

RUN mkdir /tmp/cellmaps_generate_hierarchy
COPY ./ /tmp/cellmaps_generate_hierarchy/
RUN pip install /tmp/cellmaps_generate_hierarchy

RUN rm -rf /tmp/cellmaps_generate_hierarchy

ENTRYPOINT ["/opt/conda/bin/cellmaps_generate_hierarchycmd.py"]

CMD ["--help"]
