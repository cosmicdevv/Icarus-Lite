# Icarus-Lite
Icarus Lite is a lightweight and easy-to-use version of the ChromeOS unenrollment exploit known as Icarus, which unenrolls devices with device management interception using a proxy and a custom Certificate Authority.

Icarus Lite is based off the [original Icarus](https://github.com/MunyDev/icarus) code and works in the same way. Although the original Icarus is currently archived and no longer recieving support, Icarus Lite will be supported and updated.
> [!IMPORTANT]
> As of 3/24/25, Icarus Lite is fully functional and works with prebuilt shims from [kxtz's file host](https://dl.kxtz.dev/ChromeOS/shims/Icarus) and/or [fanqyxl's file host](https://dl.fanqyxl.net/ChromeOS/Preb<uilts/Icarus). Please use the automatic certificate downloader for best results.
## Warnings
> [!IMPORTANT]
> Icarus AND Icarus Lite <b>only</b> work on ChromeOS versions 125-129 <and> kernel version 4 or below (kernel version only applies if you need to change versions). If you are not in the range of compatible versions, please upgrade/downgrade to a compatible version to use Icarus.

> [!IMPORTANT]
> <b>Do not use any public Icarus proxies.</b> Icarus can be used maliciously to remotely manage and track devices. Icarus Lite is intended to be simple to use, and self-hosting Icarus Lite is heavily advised over using any public proxies.

> Icarus Lite does <b>NOT</b> currently have functionality to build Icarus shims. Please download a prebuilt shim to use Icarus Lite, or refer an Icarus fork for information on manually building shims.

## Dependencies
Using the Windows pre-compiled .exe version of Icarus Lite, you will not need to worry about dependencies as they are packaged with the .exe. Icarus Lite uses:

- [protobuf](https://pypi.org/project/protobuf/)
- [requests](https://pypi.org/project/requests/)
- [PyOpenSSL](https://pypi.org/project/pyOpenSSL/)
- [cryptography](https://pypi.org/project/cryptography/)

As shown in Setup Instructions, these packages can be installed simultaneously by utilizing requirements.txt.

## Setup Instructions
### Windows
If you are on Windows, you can download a pre-compiled .exe version of Icarus Lite in the "Releases" section of this repository. Alternatively, you can follow the Linux/Mac instructions below to manually run Icarus Lite on your machine.
### Linux/Mac
If you are on Linux or Mac (or wish to run Icarus Lite from its source directly on Windows), the below instructions will cover how to run Icarus Lite.
1. Open a Command Prompt/Terminal window and run ``python --version`` and/or ``python3 --version``. If the command is not found, install Python from [python.org](https://python.org/downloads) (or wherever/however is best for your OS/distro). Once Python has been installed, <b>close and re-open a new terminal.</b>
2. Run ``git --version``. If the command is not found, install Git from [git-scm.com](https://git-scm.com/downloads) (or wherever/however is best for your OS/distro). Once Git has been installed, <b>close and re-open a new terminal.</b>
3. In whichever directory you want to copy Icarus Lite into, run ``git clone https://github.com/cosmicdevv/Icarus-Lite.git``, then run ``cd Icarus-Lite``.
4. Install all Python package dependencies, which can be done by running ``pip install -r requirements.txt``/``pip3 install -r requirements.txt``. On some Linux distros (specifically in managed environments), pip may not work correctly, in which case you may need to use ``sudo apt install python3-protobuf python3-requests python3-openssl python3-cryptography``.
5. Run ``python main.py`` and/or ``python3 main.py``.
6. Icarus Lite will attempt to automatically set up the required file structure and download the latest SSL certificates from kxtz's Icarus fork.
<details>
  <summary>Icarus Lite failing to download certificates?</summary>
  
  You will need to manually download the certificates from a proper source (recommended to use [kxtz's Icarus fork](https://git.kxtz.dev/kxtzownsu/httpmitm/src/branch/main/configs/m.google.com/public)) and place them into ``Icarus Lite/manualcerts``.
</details>

## Usage Instructions
Once Icarus Lite is running, usage is extremely simple. <b>Icarus Lite will attempt to automatically fetch your local IP when the Proxy Server starts, and will provide you with an IP and port to use.</b> Using Icarus Lite on the target ChromeOS device is the same process as using normal Icarus assuming the device's Stateful Partition has already been modified by an Icarus shim. <b>The target ChromeOS device should be on the SAME network as the device hosting the Icarus Lite server.</b>
1. After rebooting into ChromeOS verified mode following using an Icarus shim, <b>do not click "continue"</b>. Instead, manually open the Network Configuration by clicking on the bottom-right icons which contain the time, WiFi, and Battery status. Once in Network Configuration, connect to your WiFi and enter the proxy settings.
2. Set "Connection Type" to Manual
3. Set the "Secure HTTP" IP address to the IP Icarus Lite gives you
4. Set the "Secure HTTP" port to the port Icarus Lite gives you
5. Click "Save"
6. Resume the ChromeOS setup process as normal and Icarus Lite should unenroll you.
<details>
  <summary>Device still enrolling/getting "Can't reach Google"?</summary>
  
  - Make sure that Icarus Lite is recieving and handling the ChromeOS device's requests; check the terminal/window where Icarus Lite is running for any output past "Icarus LITE is running on...". If nothing else has been output, it means Icarus Lite isn't recieving requests from the Chromebook and therefore is not handling them accordingly. In this case:
  - Re-run the Icarus shim and ensure the target ChromeOS device and the device hosting the proxy are on the <b>SAME</b> WiFi network.
  - Ensure the shim used on the target ChromeOS device was built with the same CA (Certificate Authority) used to generate the SSL certificates

    - If you're using a prebuilt shim and don't know what CA was used, consider building your own shim and SSL certificates if nothing else works.
  - It is also important to note being above ChromeOS v130 or below ChromeOS v125 will cause the target ChromeOS device to reject the connection to the MiniServer, causing the "Can't reach Google" screen.
</details>

## Prebuilt Shim Downloads
Icarus Lite only replaces the server functionality of Icarus, but for Icarus to successfully unenroll a ChromeOS device, that device still must have had an Icarus shim ran on it. Icarus Lite does not currently have the functionality to build shims, so users must either use prebuilt shims or build their own shims from Icarus's original source. Instructions on building shims, along with a maintained fork of Icarus, can be found [here](https://github.com/fanqyxl/icarus?tab=readme-ov-file#setup-and-installation-instructions).

For prebuilt shims, it is recommended to download them from the below servers:
- [kxtz's download server](https://dl.kxtz.dev/)
- [fanqyxl's download server](https://dl.fanqyxl.net/)

## SSL Certificates
In order for the client (target ChromeOS device) to establish a proper connection to the MiniSever, we need an SSL certificate to establish the secure tunnel. If the SSL certificate is invalid, the target device will reject the connection (which in most cases will bring you to a "Cannot reach Google" screen). Icarus uses a custom CA (Certificate Authority) which isn't trusted to external devices, which also means any SSL certificates generated from our custom CA will also not be trusted to external devices. This causes most devices (including any ChromeOS devices) to reject the connection because of the untrusted CA.

This is why a user must run an Icarus shim on a ChromeOS device prior to using the Icarus Lite server for unenrollment; in the simplest terms, the shim makes the device trust the CA so that way the device won't refuse the connection to the MiniServer.

When a shim has been built using a different CA than the SSL certificates, the target device will still reject the connection. This is why if constantly getting a "Can't reach Google" screen, users should consider building their own shim and SSL certificates.

### Generating SSL certificates
Icarus Lite has the ability to automatically generate SSL certificates with a provided CA (Certificate Authority). The process is relatively simple:
1. Generate your CA (you must have a key and pem) or use an [existing CA](https://git.kxtz.dev/kxtzownsu/Icarus-Lite).
2. Put your CA (key and pem) into ``IcarusLite/manualcerts`` with the names ``myCA.pem`` and ``myCA.key``.
3. In ``IcarusLite/manualcerts``, create two empty files named ``google.com.pem`` and ``google.com.key``.
4. Run Icarus Lite and when prompted to select certificate options, select option 1 (Use manual certificates).
5. Icarus Lite will attempt to check the validity of the certificates, and will ask you if you want to generate new certificates.
6. Select ``yes`` and wait for the SSL certificates to be generated.

## Configuration
Upon first setup, Icarus Lite will automatically create and set a ``config.json`` file which will store certain configuration options designed for debugging Icarus Lite. The file can be directly edited to store ``true`` or ``false`` values for each configuration option, and the config will be loaded the next time Icarus Lite starts.

### What is the configuration for?
Configuration can be ignored by most users and is designed for enhanced server hosting if you plan to host your own server to use Icarus Lite on a larger number of devices.

### Configuration Options
- ``bypassCA``: This option, if set to ``true``, will bypass Icarus Lite requiring a CA in addition to SSL certificates. It will also disable SSL certificate validation.
- ``autoUpdate``: This option, if set to ``true``, will automatically update Icarus Lite when an update is detected and bypass asking the user yes or no.
- ``autoCertificateMode``: This option, if set to ``1`` or ``2``, will automatically select the certificate mode and bypass asking the user for a selection. Its default value is ``0``, where it will not affect anything.
- ``disableDelays``: This option, if set to ``true``, will disable the 5-second delays between intialization sections of Icarus Lite.

## Future Updates
This section contains planned updates to Icarus Lite to improve functionality.
- Shim building implementation
- fix miniservers idk why we need multiple miniservers ill change that sometime

## Credits
- [cosmicdevv](https://github.com/cosmicdevv) - Writing and maintaining Icarus Lite
- [kxtzownsu](https://github.com/kxtzownsu) - Maintaining the Certificate Authority Icarus Lite uses
- [Fanqyxl](https://github.com/fanqyxl) - Emotional support + keyrolling his chromebook lol
- [MunyDev](https://github.com/MunyDev) - Discovering and creating original Icarus
