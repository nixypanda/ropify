# Ropify: The Simple Rope CLI Wrapper for Editors

NOTE: This is a fork of the original which caters to my specific needs at the moment.

Ropify is a CLI tool streamlining the experience of leveraging [Rope](https://github.com/python-rope/rope) to refactor Python code, designed to be used as an API for editors like Vim/Neovim[^1].

Made for developers who prefer a streamlined approach, Ropify is an ideal choice for those hesitant about installing [ropevim](https://github.com/python-rope/ropevim) due to its heavy requirements or vimscript foundation.
If you find ropevim's exhaustive features a tad much and are in pursuit of a more minimalist alternative, look no further than Ropify!

## Getting Started 🚀

Follow the instructions below to set up `ropify`:

```sh
# Set up a virtual environment for Ropify
python -m venv ~/.venvs/ropify
source ~/.venvs/ropify/bin/activate
# Clone the Ropify repository
git clone https://github.com/niqodea/ropify.git ~/ropify
# Navigate into the cloned directory
cd ~/ropify
# Install Ropify
pip install .
# Ensure Ropify is accessible outside the virtual environment
ln -s $(which ropify) ~/.local/bin/
```

Ropify should now be set up and ready to use.
You can verify the installation with:

```sh
ropify --help
```

After the setup, integrate the commands in `nvim-bindings.lua` into your Neovim config to use Ropify from your editor.[^2]

## Current Commands 🔍

- `ropify move-symbol-by-name`: Move class or function to another module (provide the name of the symbol to move)
- `ropify move-symbol-by-offset`: Move class or function to another module (provide the offset of the symbol to move)
- `ropify move-module`: Move module to another package.
- `ropify rename-module`: Rename a module
- `ropify fixup-imports`: move-symbol\* moves a symbol with import of the form `import a.b.c`, this command changes it to `from a.b.c import <symbol name>`. I find it cleaner.

[^1]: The CLI's user experience is also influenced by the rope APIs, which are primarily designed with editor integrations in mind.
[^2]: TODO: Add vimscript bindings.
