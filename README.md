<a name="readme-top"></a>

<!-- Presentation Block -->
<br />

<div align="center">

  <a href="https://github.com/LightDestory/PlexNFSWatchdog">
    <img src="https://raw.githubusercontent.com/LightDestory/PlexNFSWatchdog/master/.github/assets/images/presentation_image.png" alt="Preview" width="90%">
  </a>

  <h2 align="center">Plex NFS Watchdog</h2>
  
  <p align="center">
      A utility to trigger Plex partial-scans on NFS configurations, on which inotify is not supported
  </p>
  
  <br />
  <br />
</div>

<!-- ToC -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#book-about-the-project">📖 About The Project</a>
    </li>
    <li>
      <a href="#gear-getting-started">⚙️ Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#usage">Usage</a></li>
        <li><a href="#notes">Notes</a></li>
      </ul>
    </li>
    <li><a href="#dizzy-contributing">💫 Contributing</a></li>
    <li><a href="#handshake-support">🤝 Support</a></li>
    <li><a href="#warning-license">⚠️ License</a></li>
    <li><a href="#hammer_and_wrench-built-with">🛠️ Built With</a></li>
  </ol>
</details>

<!-- About Block -->

## :book: About The Project

Inotify is a Linux kernel subsystem that allows monitoring changes to files and directories in real-time. It is commonly used by applications to watch for changes in files or directories and respond accordingly.

Plex makes use of inotify to perform partial scans when a file is added or removed from a directory. This allows Plex to update its library without having to perform a full scan.

Running Plex Media Server with the library located on Network File System (NFS) mounted directories will not trigger such partial scans because inotify doesn't work on NFS. When a file is changed on an NFS mount, it doesn't trigger an inotify event on the client side.

`Plex NFS Watchdog` is a utility that can be installed on the machine that produces inotify to monitors directories for changes and triggers a partial scan on the Plex Media Server instance installed in a different machine when a change is detected by invoking the Plex API.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Setup Block -->

## :gear: Getting Started

To use `Plex NFS Watchdog` you must ensure that on all machines involved the Plex's Library sections use the same folder name. _The folder path can be different on each machine, but the folder name must be the same._

This is important because the utility will use the folder name to trigger the partial scan.

For example, if you have a library section called "Movies" and the folder name is "Movies", the utility will trigger a partial scan on the "Movies" library section when a change is detected in the "Movies" folder.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Prerequisites

Obtain the Plex Authentication Token for your Plex Media Server instance. You can find instructions on how to do this [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

You can install this tool as a Python Module using `pip`
or executing the script directly.

- If you want to install the tool as a Python Module:
    - Install the module using pip: `pip install plex-nfs-watchdog`
    - You can run the tool using: `plex-nfs-watchdog`
- If you want to use the script directly:
    - Clone the repository anywhere on your pc:

      `git clone https://github.com/LightDestory/PlexNFSWatchdog`

    - Install the requirements using `pip` (create a `venv` if you want):

      `pip install -r requirements.txt`

    - Run directly from source:

      `python ./src/plex_nfs_watchdog/plex_nfs_watchdog.py`

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Usage

This utility requires the following arguments to work:

| Argument                                               | Role                                                                                                                                   |
|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| __--scan \| -s__                                       | Manually triggers a partial-scan on the given paths                                                                                    |
| __--daemon \| -d__                                     | Starts a watchdog daemon to automatically triggers a partial-scan on the given paths <br> __Requires:__ _--interval_ and _--listeners_ |
| __--paths \| -p__ _\[PATHS...\]_                       | A list of folder paths                                                                                                                 |
| __--host \| -H__ _HOST_                                | The host of the Plex server<br>__Default:__ _http://localhost:32400_                                                                   |
| __--token \| -t__ _TOKEN_                              | The token of the Plex server                                                                                                           |
| __--interval \| -i__ _INTERVAL_ \[OPTIONAL\]           | The interval in seconds to wait between partial-scans                                                                                  |
| __--listeners \| -l__ _\[LISTENERS...\]_  \[OPTIONAL\] | The event type to watch: `move`, `modify`, `create`, `delete`, `io_close`, `io_open`                                                                                                        |

- Manual Scan example:
    >`plex-nfs-watchdog --scan --paths /path/to/library_section1/section_chield1 --host http://localhost:32400 --token YOUR_TOKEN`
- Daemon Scan example:
  >`plex-nfs-watchdog --daemon --paths /path/to/library_section1 --host http://localhost:32400 --token YOUR_TOKEN --interval 150 --listeners move modify create delete`

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Notes

After the first successful run, a cache config file containing Plex's host and token will be created in the user's home directory. This file will be used for subsequent runs, so you don't have to provide them every time.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Contribute Block -->

## :dizzy: Contributing

If you are interested in contributing, please refer to [Contributing Guidelines](.github/CONTRIBUTING.md) for more information and take a look at open issues. Ask any questions you may have and you will be provided guidance on how to get started.

Thank you for considering contributing.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Support Block -->

## :handshake: Support

If you find value in my work, please consider making a donation to help me create, and improve my projects.

Your donation will go a long way in helping me continue to create free software that can benefit people around the world.

<p align="center">
<a href='https://ko-fi.com/M4M6KC01A' target='_blank'><img src='https://raw.githubusercontent.com/LightDestory/RepositoryTemplate/master/.github/assets/images/support.png' alt='Buy Me a Hot Chocolate at ko-fi.com' width="45%" /></a>
</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- License Block -->

## :warning: License

The content of this repository is distributed under the GNU GPL-3.0 License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Built With Block -->

## :hammer_and_wrench: Built With

- [Python](https://www.python.org/)
- [Watchdog](https://pypi.org/project/watchdog/)
- [PlexAPI](https://pypi.org/project/PlexAPI/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
