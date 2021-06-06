# Open Toontown
This repository contains the code for Open Toontown, based on the latest version of Disney's Toontown Online (sv1.0.47.38).

## Setup
After cloning the repository, you will need to clone the [resources](https://github.com/open-toontown/resources) repository inside the directory where you cloned the source repo.

Secondly, you would have to install and use a specific version of Panda3D, which includes `libotp` and `libtoontown`.  You can use the prebuilt installers for your operating system here:

[Panda3D SDK for Windows (x86)](https://drive.google.com/file/d/1sF4QLDl6h5ZRX-LMAftslDNpkJ-pF9SR/view?usp=sharing)

[Panda3D SDK for Windows (x86_64)](https://drive.google.com/file/d/1TEdJ6D3W9ZUf883dg1FWDDPCInepImiz/view?usp=sharing)

**WINDOWS USERS:** If you install Panda3D outside the default directory (or use the x86 installer), you may have to change the `PPYTHON_PATH` file located in the root directory and change it to your install directory.

If you use Linux, or are interested in building Panda3D yourself, head on over to [our Panda3D fork](https://github.com/open-toontown/panda3d) and read the "Building Panda3D" section on the README file there.

To start the server and run the game locally, go to your platform directory (`win32` for Windows, `darwin` for Mac and `linux` for Linux), and make sure you start the following scripts in order:

`Astron Server -> UberDOG (UD) Server -> AI (District) Server -> Game Client`

Be sure to wait till the servers have finished booting before starting the next.  If everything's done correctly, you should be able to make your toon and play the game!  There is no support for Magic Words (commands) yet, [but it is currently in the works!](https://github.com/open-toontown/open-toontown/projects/1)

## Contributing
Submitting issues and Pull Requests are encouraged and welcome.

How you commit changes is your choice, but when committing, please include what you did as well as a basic description, just so we know exactly what you did. Here are some examples:

* `minigames: Fix crash when entering the trolley`
* `racing: Fix possible race condition when two racers tied`
* `golf: Refix wonky physics once and for all (hopefully)`
