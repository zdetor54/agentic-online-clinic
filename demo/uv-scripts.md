
# Running scripts with UV

For these, copy past the python code into `demo.py`, save and then execute the command listed above each codeblock.

## Hello world

uv run demo.py

```python
print('hello world')
```

## With tqdm

uv run --with tqdm demo.py

```python
import time
from tqdm import tqdm

for i in tqdm(range(20)):
    time.sleep(0.05)
```

## Requirements defined in file

uv run demo.py

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#  "tqdm"
# ]
# ///
import time
from tqdm import tqdm

for i in tqdm(range(20)):
    time.sleep(0.05)
```

### File as an executable

chmod +x demo.py
./demo.py

```python
#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#  "tqdm"
# ]
# ///
import time
from tqdm import tqdm

for i in tqdm(range(20)):
    time.sleep(0.05)
```
