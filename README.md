# Koillection-tools

## Setup env

1) Enter project directory
2) `project python`
3) Edit Python version in `flake.nix` and Python version + dependencies in `pyproject.toml`
4) `uv lock`
5) `direnv reload`

## Usage

fill `credentials.txt` as your koillection credentials:

```
username: xxx
password: yyy
```

use `get.py` to download a card list from https://limitlesstcg.com, for example https://limitlesstcg.com/cards/BS.
The run `post.py` and give it the link to your koillection wishlist and the csv created when prompted.
