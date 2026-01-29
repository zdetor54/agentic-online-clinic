# Installing / managing python versions in uv

## Install specific version of python

> These in general are not needed, as uv installs the correct version of python if it's listed in the project `.python-version` file

```bash
uv python list               # see list of installed python versions
uv python install 3.12.9     # installs specific version of python
```

## Test updating project python version

Change the python version in `.python-version` to something else and run the below command. You should see uv download a new version of python, then runs your code.

```bash
uv run streamlit run ui/app.py
```
