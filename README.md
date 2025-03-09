# Icarus-Lite
Icarus Lite is a lightweight and easy-to-use version of the ChromeOS unenrollment exploit known as Icarus, which unenrolls devices with device management interception using a proxy and a custom Certificate Authority.
<br>
> Icarus Lite is based off the [original Icarus](https://github.com/MunyDev/icarus) code and works in the same way. Although the original Icarus is currently archived and no longer recieving support, Icarus Lite will be supported and updated.
## Warnings
> [!IMPORTANT]
> Icarus AND Icarus Lite <b>only</b> work on ChromeOS versions between v125 and v130. If you are above v130 or below v125, please downgrade (or update/upgrade) to a version Icarus/Icarus Lite will work with.
- As of 3/9/25, Icarus Lite has been tested and confirmed to work. kxtz does NOT currently provide the CA used to generate downloaded shims; as such, please wait for kxtz to pre-build shims OR build your own CA, shims, and certificates to use with Icarus Lite.
- Icarus AND Icarus Lite <b>only</b> work on ChromeOS versions below 130. If you are above v130, please downgrade to use Icarus/Icarus Lite.
- Do not use any public Icarus proxies. Icarus can be used maliciously to remotely manage and track devices. Icarus Lite is intended to be simple to use, and self-hosting Icarus is heavily advised over using any public proxies.
- Icarus Lite does <b>NOT</b> currently have functionality to build Icarus shims. Please download a prebuilt shim to use Icarus Lite, or refer an [Icarus fork](https://github.com/fanqyxl/icarus/tree/main) for information on manually building shims.

## Dependencies
Icarus Lite, following its intended purpose of being lightweight and simple, only utilizes two external dependencies. Using the Windows pre-compiled .exe version of Icarus Lite, you will not need to worry about dependencies as they are packaged with the .exe. Icarus Lite uses:

- [protobuf](https://pypi.org/project/protobuf/)
- [requests](https://pypi.org/project/requests/)

## Setup Instructions
### Windows
If you are on Windows, you can download a pre-compiled .exe version of Icarus Lite in the "Releases" section of this repository. Alternatively, you can follow the Linux/Mac instructions below to manually build Icarus on your machine.
### Linux/Mac
If you are on Linux or Mac (or wish to run Icarus Lite from its source directly on Windows), the below instructions will cover how to run Icarus Lite.
1. Open a Command Prompt/Terminal window and run ``python --version`` and/or ``python3 --version``. If the command is not found, install Python from [python.org](https://python.org/downloads) (or wherever/however is best for your OS/distro). Once Python has been installed, <b>close and re-open a new terminal.</b>
2. Install the ``protobuf`` and ``requests`` Python package, which can be done by running ``pip install protobuf``/``pip3 install protobuf`` and ``pip install requests``/``pip3 install requests``. On some Linux distros (specifically in managed environments), pip may not work correctly, in which case you may need to use ``sudo apt install python3-protobuf python3-requests``.
3. Run ``git --version``. If the command is not found, install Git from [git-scm.com](https://git-scm.com/downloads) (or wherever/however is best for your OS/distro). Once Git has been installed, <b>close and re-open a new terminal.</b>
4. In whichever directory you want to copy Icarus Lite into, run ``git clone https://github.com/cosmicdevv/Icarus-Lite.git``, then run ``cd Icarus-Lite``.
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

## Certificates
In order for the client (target ChromeOS device) to establish a proper connection to the MiniSever, we need an SSL certificate to establish the secure tunnel. If the SSL certificate is invalid, the target device will reject the connection (which in most cases will bring you to a "Cannot reach Google" screen). Icarus uses a custom CA (Certificate Authority) which isn't trusted to external devices, which also means any SSL certificates generated from our custom CA will also not be trusted to external devices. This causes most devices (including any ChromeOS devices) to reject the connection because of the untrusted CA.

This is why a user must run an Icarus shim on a ChromeOS device prior to using the Icarus Lite server for unenrollment; in the simplest terms, the shim makes the device trust the CA so that way the device won't refuse the connection to the MiniServer.

When a shim has been built using a different CA than the SSL certificates, the target device will still reject the connection. This is why if constantly getting a "Can't reach Google" screen, users should consider building their own shim and SSL certificates.

SSL certificates can be generated using [generate_ssl_certificate.sh](https://github.com/fanqyxl/icarus/blob/main/httpmitm/generate_ssl_certificate.sh) once a CA has been generated.

## Future Updates
This section contains planned updates to Icarus Lite to improve functionality.
- Shim building implementation

## Credits
- [cosmicdevv](https://github.com/cosmicdevv) - Writing and maintaining Icarus Lite
- [MunyDev](https://github.com/MunyDev) - Discovering and creating original Icarus
- [kxtzownsu](https://github.com/kxtzownsu) - Maintaining certificates Icarus uses
