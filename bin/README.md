Everything in here will end up in the host OS' path so it can be executed
directly, example:

    $ kalite start

Since the kalite command resolves many different things like where kalite is
installed and which python interpretor to run, you might wanna look a
different place for implementing new things :)

## Windows

Have a look in the `windows/` directory, there's some stuff for you. Also,
change your operating system :P

To have the new command `kalite` registered, double-click or execute
`windows/setup.bat`.

To run directly (assuming you're in the root folder), use `python.exe bin/kalite`.