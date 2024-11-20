# ti-chatbot-workshop
Repository used for the T&amp;I conference: **Smart Chatbot Workshop**

## Installation

1. Make sure you have python installed on your machine. We recommend using `pyenv` to manage different python versions in WSL and `pyenv-win` to manage it on Windows.
[pyenv  installation](https://github.com/pyenv/pyenv-installer), [pyenv-win installation](https://github.com/pyenv-win/pyenv-win#installation)
2. After installing the tool run
```
pyenv update
pyenv install --list
```
This gives you a list of python versions that can be installed. This repository has been tested with `3.12.5` version.
```
pyenv install 3.12.5
pyenv global 3.12.5
```
3. Create a virtual environment to isolate the dependencies
```
python -m venv .venv
````
Activate the virtual environment
```cmd
# on mac / linux
source .venv/bin/activate
# on windows
.venv\Scripts\activate
```
4. Install the required packages
```cmd
pip install -r requirements.txt
```

## Run application

WIP
