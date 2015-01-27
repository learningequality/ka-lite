Everything in here will end up in the host OS' path so it can be executed
directly, example:

    $ kalite start

Since the kalite command resolves many different things like where kalite is
installed and which python interpretor to run, you might wanna look a
different place for implementing new things :)

## Distributing on Mac/OSX

Rather than running the executable directly, you can also:

1. Symlink it from somewhere in your path, e.g.
   
       cd /usr/bin
       ln -s /path/to/kalite/bin/kalite .

2 . Copy `kalite` (the file in `bin/`) directly to `/usr/bin`. This is probably
    what you want to do for a distribution. Then, you need to setup the following
    env variables: 
    
    - KALITE_DIR: The root directory of the installation
    - KALITE_PYTHON: If you want kalite run with a diffent python than the one
      in your path (optional) or if `python` is not found in the system's path.


## Windows

Have a look in the `windows/` directory, there's some stuff for you. Also,
change your operating system :P

To have the new command `kalite` registered, double-click or execute
`windows/setup.bat`.

To run directly (assuming you're in the root folder), use `python.exe bin/kalite`.

### Distributing for Windows

Make sure that during the installation, the `bin/windows/setup.bat` command
is run.