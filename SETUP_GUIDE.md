# Windows Setup Guide: NLTK, TextBlob, and LangChain

This guide uses Windows PowerShell and a project-specific virtual environment.
Python 3.10 or 3.11 is a conservative choice when working with the pinned packages
in this project.

## 1. Check Python

Open PowerShell and run:

```powershell
py --version
py -m pip --version
```

If `py` is unavailable, install Python from
[python.org](https://www.python.org/downloads/windows/). During installation, enable
**Add python.exe to PATH** and install the Python launcher.

## 2. Create and activate a virtual environment

Move into the project directory, then create an isolated environment:

```powershell
cd path\to\ai-customer-emotion-intent-predictor
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The prompt should now begin with `(.venv)`. Upgrade the packaging tools:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Using `python -m pip` is preferable to a bare `pip` command because it makes the
Python environment receiving the package explicit.

## 3. Install the libraries

### Install from this project's requirements file

The recommended method installs the project's exact, pinned versions:

```powershell
python -m pip install -r requirements.txt
```

### Install each library separately

If you are working outside this project, install the packages individually:

```powershell
python -m pip install nltk==3.9.1
python -m pip install textblob==0.19.0
python -m pip install langchain==0.3.27 langchain-openai==0.3.27 openai==1.93.0
```

`langchain-openai` is the separate integration package used to connect current
LangChain applications to OpenAI models.

Confirm that the installations belong to the active environment:

```powershell
python -m pip show nltk textblob langchain langchain-openai openai
```

## 4. Download the NLTK VADER sentiment lexicon

VADER's Python code and its language data are distributed separately. Download the
required lexicon once for the current Windows user:

```powershell
python -m nltk.downloader vader_lexicon
```

The NLTK downloader's package identifier is `vader_lexicon`. In Python, the missing
resource may be reported using the longer path `sentiment/vader_lexicon.zip`.

An equivalent programmatic download is:

```powershell
python -c "import nltk; nltk.download('vader_lexicon')"
```

Verify VADER:

```powershell
python -c "from nltk.sentiment import SentimentIntensityAnalyzer; print(SentimentIntensityAnalyzer().polarity_scores('The support was excellent!'))"
```

The result should contain `neg`, `neu`, `pos`, and `compound` scores.

### Use a custom NLTK data directory

This is useful on managed computers where the default user directory is not
writable:

```powershell
New-Item -ItemType Directory -Force C:\nltk_data
python -m nltk.downloader -d C:\nltk_data vader_lexicon
$env:NLTK_DATA = "C:\nltk_data"
```

To preserve that setting for future terminals:

```powershell
[Environment]::SetEnvironmentVariable("NLTK_DATA", "C:\nltk_data", "User")
```

Open a new PowerShell window after setting a persistent environment variable.

## 5. Download TextBlob corpora

Install the corpora used by TextBlob's standard NLP features:

```powershell
python -m textblob.download_corpora
```

For a smaller download containing only the corpora needed for basic features:

```powershell
python -m textblob.download_corpora lite
```

Use the full download unless storage or network policy is restrictive. TextBlob
uses NLTK internally, so its corpora are stored in an NLTK data directory.

Verify TextBlob sentiment analysis:

```powershell
python -c "from textblob import TextBlob; print(TextBlob('The support was excellent!').sentiment)"
```

## 6. Verify LangChain

This import check does not make a network request:

```powershell
python -c "import langchain; from langchain_openai import ChatOpenAI; print(langchain.__version__)"
```

To call an OpenAI model, set the API key for the current PowerShell session:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

Do not place a real key in source code or commit it to Git. A minimal connection
test is:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
reply = model.invoke("Reply with exactly: connection successful")
print(reply.content)
```

Model availability depends on the OpenAI account and may change. Substitute a
model that is enabled for your project if necessary.

## 7. Common errors and fixes

### `py` or `python` is not recognized

- Re-run the Python installer and enable the PATH option and Python launcher.
- Close and reopen PowerShell after installation.
- Try `py` when `python` fails, or use Python's full installed path.
- Disable the Microsoft Store aliases under **Manage app execution aliases** if
  Windows opens the Store instead of Python.

### PowerShell says script execution is disabled

Activation can fail with a `PSSecurityException`. Allow locally created scripts for
your Windows user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

If company policy prevents this change, skip activation and call the environment's
Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### `No module named nltk`, `textblob`, or `langchain`

The package was probably installed into a different Python environment. Check:

```powershell
python -c "import sys; print(sys.executable)"
python -m pip --version
python -m pip list
```

Both commands should point inside `.venv`. Reinstall with `python -m pip` while the
environment is active.

### NLTK raises `LookupError: Resource vader_lexicon not found`

Download it using the same Python that runs the application:

```powershell
python -m nltk.downloader vader_lexicon
```

If it was downloaded elsewhere, print the searched locations:

```powershell
python -c "import nltk; print('\n'.join(nltk.data.path))"
```

Move the data to one of those locations or set `NLTK_DATA` to the directory that
contains it. Restart Streamlit or the Python process afterward.

### TextBlob raises `MissingCorpusError`

Run:

```powershell
python -m textblob.download_corpora
```

If the error names a specific NLTK resource, download that identifier directly:

```powershell
python -m nltk.downloader RESOURCE_NAME_FROM_THE_ERROR
```

Recent NLTK releases may request resources such as `punkt_tab` rather than `punkt`;
use the exact identifier shown in the exception.

### `cannot import name ChatOpenAI from langchain...`

OpenAI integrations live in `langchain-openai`. Install it and use the current
import:

```powershell
python -m pip install langchain-openai==0.3.27
```

```python
from langchain_openai import ChatOpenAI
```

Avoid older examples that import `ChatOpenAI` directly from `langchain`.

### OpenAI authentication or model errors

- `AuthenticationError`: confirm `$env:OPENAI_API_KEY` is set in the terminal that
  starts the application, and rotate the key if it may have been exposed.
- `model_not_found`: choose a model available to the OpenAI project tied to the key.
- `RateLimitError`: check project billing and usage limits, then retry transient
  failures with exponential backoff.
- A ChatGPT subscription and API billing are separate; a subscription does not by
  itself provide API credits.

### SSL, certificate, proxy, or timeout errors during installation/download

- Confirm the computer's date and time are correct.
- Upgrade `pip` and the certificate bundle:

  ```powershell
  python -m pip install --upgrade pip certifi
  ```

- On a corporate network, ask the administrator for the approved proxy and root
  certificate. Configure those rather than disabling TLS verification.
- If packages install but corpus downloads fail, the firewall may allow PyPI while
  blocking NLTK's data host; use an administrator-approved connection or manually
  place downloaded data in an NLTK data directory.

### Dependency conflicts after installing other packages

Start with a clean environment and reinstall the pinned file:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Only remove `.venv`; do not remove the project source files. `pip check` should
report that no broken requirements were found.

## 8. Final verification checklist

Run these commands from the activated environment:

```powershell
python -m pip check
python -c "from nltk.sentiment import SentimentIntensityAnalyzer; print(SentimentIntensityAnalyzer().polarity_scores('Great service'))"
python -c "from textblob import TextBlob; print(TextBlob('Great service').sentiment)"
python -c "import langchain; from langchain_openai import ChatOpenAI; print('LangChain', langchain.__version__)"
```

If all four commands succeed, the local libraries and language resources are ready.

## Official references

- [Installing NLTK](https://www.nltk.org/install.html)
- [Installing NLTK data](https://www.nltk.org/data.html)
- [Installing TextBlob](https://textblob.readthedocs.io/en/dev/install.html)
- [LangChain Python documentation](https://python.langchain.com/docs/introduction/)

