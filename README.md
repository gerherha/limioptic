# Easy installation:
Python version >=3.7,<3.10 required. 3.8 is used in this example. 

**WINDOWS:** Shared dlls are 32 bit only, so 32 bit version of python is required.

## using pipx
1. install [pipx](https://github.com/pypa/pipx): `python3.8 -m pip install pipx --user`
2. install limioptic: `pipx install limioptic`
3. start limioptic from everywhere with `limioptic`

## pipenv
1. `python3.8 -m pipenv shell`
2. `pipenv install limioptic`
3. `limioptic` or `pipenv run limioptic`

## poetry
1. `poetry init`
2. Python version `>=3.7,<3.10`
3. `poetry add limioptic`
4. `limioptic` or `poetry run limioptic`

## globally (the messy way)
1. `python3.8 -m pip install limioptic --prefer-binary`
2. `limioptic` or `python -m limioptic`

you can also run limioptic as a module

<br>

**The source code in this repo will be updated soon. At the moment the master branch contains huge blobs. So keep that in mind before cloning. `git-filter-branch` will come to the rescue soon ;)**


<br>
<b>Introduction:</b>

A short introducion can be found at <a href="http://alexander-stolz.github.io/limioptic/">www.limioptic.de</a>.

<br>
<b>Licence</b>

The program LIMIOPTIC maintained by Alexander Stolz is freely available and distributable. However, if you use it for some work whose results are made public, then you have to reference it properly.
