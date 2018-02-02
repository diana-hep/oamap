#!/usr/bin/env python

import os

if os.environ["TRAVIS_PYTHON_VERSION"] == "2.6":
    miniconda = False

elif os.environ["TRAVIS_PYTHON_VERSION"] == "2.7":
    miniconda = True
    os.system("wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O miniconda.sh")

else:
    miniconda = True
    os.system("wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh")

if miniconda:
    os.system("bash miniconda.sh -b -p {0}/miniconda".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/conda config --set always_yes yes --set changeps1 no".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/conda update -q conda".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/conda info -a".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION numba".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/source activate test-environment".format(os.environ["HOME"]))
    os.system("{0}/miniconda/bin/python setup.py install".format(os.environ["HOME"]))
