"""
Icarus Lite
Written by cosmicdevv
https://github.com/cosmicdevv/Icarus-Lite

certs hosted by HarryJarry1
https://github.com/HarryJarry1/Icarus-Lite
"""
import warnings
# If on 32 bit Python, ignore Cryptography warnings (they're annoying)
warnings.simplefilter("ignore", category=UserWarning)
import os
import sys
import time
import json
import socket
import ssl
import shutil
import threading
import select
import re
import subprocess
import http.server
import urllib.parse
import requests
import OpenSSL.crypto
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timezone, timedelta
from dmbackend import device_management_pb2

"""
GLOBAL VARIABLES
"""
version = "1.1.13"
pInitial = 3001 # The port that MiniServers will start up from.
latestVersionUrl = "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/main/version.txt" # URL of the file where the latest version number is stored
scriptUrl = "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/main/main.py" # URL of the file where the latest script version is stored
sslCerts = {
    "google.com.key": "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/certs/google.com.key",
    "google.com.pem": "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/certs/google.com.pem",
    "myCA.pem": "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/certs/myCA.pem",
    "myCA.key": "https://raw.githubusercontent.com/HarryJarry1/Icarus-Lite/refs/heads/certs/myCA.key"
} # Stores names and links of certificates to download
certPaths = {} # Stores paths of certificates on the local filesystem
installationFolder = "IcarusLite" # Folder name that stores certificates
noSupport = False # If user is running with invalid certs, makes the console print extra characters so if I get an Issue on the GitHub and see the characters it means they're using invalid certs and it's on them
config = {
    "bypassCA": False,
    "autoUpdate": False,
    "autoCertificateMode": 0,
    "disableDelays": False,
}

"""
PROXY/MINISERVER FUNCTIONALITY
"""
# unlike normal icarus which calls other files and shit to create a miniserver, we can do it easily in icarus Lite!!!!!
class MiniServerHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Since we have our own logging, we don't need the HTTP server to log requests it recieves

    def do_GET(self):
        colorprint("GET request recieved, ignoring.\n\n", "blue")
        self.send_response(200)
        self.wfile.write(b"OK")
        self.miniserver.stop() # Stop the server

    def do_POST(self):
        # Slightly rewritten part of dmbackend
        # Get the body content of the request from the client
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        # Create a dmr object
        dmr = device_management_pb2.DeviceManagementRequest()
        dmr.ParseFromString(body)
        # Declare status_code and resp which are used for the response later.
        status_code = 0
        resp = None
        # all the magic originally by writable
        if (dmr.HasField("device_state_retrieval_request")):
            status_code = 200
            resp = device_management_pb2.DeviceManagementResponse()
            rr = resp.device_state_retrieval_response
            dv = device_management_pb2.DeviceInitialEnrollmentStateResponse()
            dv.Clear()
            dv = rr.initial_state_response
            dv.initial_enrollment_mode = 0
            dv.management_domain = ""
            dv.is_license_packaged_with_device = False
            dv.disabled_state.message = ""
            rr.restore_mode = 0
            rr.management_domain = ""
        else:
            con = requests.post("https://m.google.com/devicemanagement/data/api?" + urllib.parse.urlparse(self.path).query, data=body, headers=dict(self.headers))
            status_code = con.status_code
            resp = device_management_pb2.DeviceManagementResponse()
            resp.ParseFromString(con.content)
        # Send the response back to the client, which unenroll the device
        self.send_response(status_code)
        self.send_header("Content-Type", "application/x-protobuffer")
        self.send_header("Content-Length", str(len(resp.SerializeToString())))
        self.end_headers()
        self.wfile.write(resp.SerializeToString())
        colorprint("Successfully intercepted request.\n\n", "green")
        self.miniserver.stop() # Stop the server

class MiniServer:
    def __init__(self):
        # Create a mini HTTP/HTTPS server.
        global pInitial
        self.port = pInitial
        handler = MiniServerHandler
        handler.miniserver = self # Set the handler's miniserver to the miniserver lol
        self.stopped = False
        # Keep trying to create the server in case some ports are already in use, in which case the code will increment the port and try again.
        while True:
            try:
                self.httpd = http.server.HTTPServer(("0.0.0.0", self.port), handler)
                break
            except OSError:
                pInitial += 1
                self.port = pInitial
                continue
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=certPaths["pem"], keyfile=certPaths["key"])
        self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
        pInitial += 1
        self.server = threading.Thread(target=self.httpd.serve_forever, daemon=True) # Start the server in a separate thread so it doesn't block the main thread.
        self.server.start() # Start the separate thread
        def end_server(self):
            i = 0
            while i <= 15:
                i += 1
                if self.stopped:
                    break
                time.sleep(1)
            if not self.stopped:
                self.stop()
        threading.Thread(target=end_server, args=(self,)).start()
    def stop(self): # this SHOULD stop the server and the threads, PROBABLY
        if self.httpd: # If the server is running
            self.stopped = True
            self.httpd.shutdown() # Shutdown the server
            self.server.join() # wait until the thread fully stops

def handle_client(client_socket, address):
    # Initial request buffer
    colorprint("// HANDLING REQUEST \\\\\n", "blue")
    host = None
    port = 0
    is_tls = False
    is_filtered = False
    request = b""
    
    # Gets all the request data (we while loop this incase the request is larger than 1 packet, and the loop ends once the end of the request is reached)
    while b"\r\n\r\n" not in request:
        data = client_socket.recv(4096) # Recieve 1 packet with the buffer size of 4096 bytes
        request += data # Add the newly retrieved data to the stored request data

    # Split and decode the request data
    request_line = request.split(b"\r\n")[0].decode("utf-8")
    if request_line.startswith("CONNECT"): # CONNECT means it's a TLS request
        is_tls = True
        _, target, _ = request_line.split(" ", 2)
        host, port = target.split(":", 1)
        port = int(port)
    else: # If CONNECT isn't in the request_line, it's not a TLS request, and we handle it differently
        is_tls = False
        method, path, _ = request_line.split(" ", 2)
        # Get the host from the request data
        for line in request.split(b"\r\n")[1:]:
            if line.startswith(b"Host: "):
                host = line[6:].decode("utf-8")
                break
        # If a host isn't found, the request is probably malformed
        if not host:
            client_socket.close()
            return
        # If the host specifies a port to use, we'll retrieve it.
        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port) # Ensure the host is an integer and not a string
        else: # If no port is specified, we'll use the default port for a non-TLS request (which is 80)
            port = 80 

    # Check if the host is filtered
    if re.match(r"m\.google\.com", host):
        is_filtered = True

    # Console logging
    colorprint("Server Address: " + str(host), "blue")
    colorprint("Is TLS (HTTPS) connection: " + str(is_tls), "green" if is_tls else "red")
    colorprint("Is filtered? " + str(is_filtered), "green" if is_filtered else "red")

    # If it's filtered and it's a TLS request, we'll have to send the request to our own server so we can intercept it
    if is_filtered and is_tls:
        # Create a new MiniServer, 
        miniserver = MiniServer()
        # Create a server socket to communicate with the Miniserver
        miniserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        miniserver_socket.connect(("127.0.0.1", miniserver.port)) 
        # Acknowledge the request, then pipe the client to the MiniServer
        client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        try:
            pipe = tunnel_traffic(client_socket, miniserver_socket)
            # If tunnel closed on first packet (client likely rejected connection)
            if not pipe: # If pipe returned false
                colorprint("ERROR: The client may have rejected the connection. This is usually an SSL issue.", "red")
                miniserver.stop() # Stop the MiniServer since there will not be a connection.
        except Exception as e:
            colorprint(f"ERROR on request: {str(host)}\nThe client may have rejected the connection.", "red")
            colorprint("Have you ran the Icarus shim on the target Chromebook?", "blue")
            miniserver.stop() # Stop the MiniServer since there will not be a connection.
        return
    # The below only runs if the host isn't filtered (or it is filtered but not a TLS request, in which case we won't intercept it)
    try:
        # Create a connection to the host server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, port))
        if is_tls:
            # If it's a TLS request, we'll acknowledge the request so the tunnel between the client and server can be established shortly
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            # If it's not a TLS request, we'll forward all the data from the client to the server
            server_socket.sendall(request)
        # Same as .pipe() in NodeJS but we have to do it a bit differently.
        try:
            pipe = tunnel_traffic(client_socket, server_socket)
        except Exception as e:
            colorprint(f"ERROR on request: {str(host)}\nUnknown failure tunneling traffic.", "red")
    except Exception as e:
        colorprint(f"Error connecting to {host}:{port} - {e}", "red")
        client_socket.close()
        return
    print("\n\n") # New lines for next request

def tunnel_traffic(client_socket, server_socket):
    # Because Python does not have a built-in .pipe() method like NodeJS, we have to do this manually.
    client_socket.setblocking(0)
    server_socket.setblocking(0)
    while True:
        readable, _, exceptional = select.select([client_socket, server_socket], [], [client_socket, server_socket], 60)
        if exceptional:
            break
        for sock in readable:
            peer_sock = server_socket if sock is client_socket else client_socket
            # normally we'd put a try catch exception here but i want it to raise an error when there is one
            data = sock.recv(4096)
            # If there's no data, the socket closed
            if not data:
                # If it's the first packet or something, return False for error handling purposes
                if readable.index(sock) == 0:
                    return False
                return True
            first = False
            peer_sock.sendall(data)
    client_socket.close()
    server_socket.close()

"""
EXTRA FUNCTIONALITY
"""

def handleManualCertificates():
    messageDisplayed = [False, False]
    while True:
        googleKey = os.path.exists(f"{installationFolder}/manualcerts/google.com.key")
        googlePem = os.path.exists(f"{installationFolder}/manualcerts/google.com.pem")
        caKey = os.path.exists(f"{installationFolder}/manualcerts/myCA.key")
        caPem = os.path.exists(f"{installationFolder}/manualcerts/myCA.pem")
        caBypass = os.path.exists(f"{installationFolder}/manualcerts/bypassCA.txt")
        if googleKey and googlePem and caKey and caPem:
            colorprint("Manual certificates found. Using manual certificates for Icarus Lite.", "green")
            # Set the certificate paths to the manualcerts path
            certPaths["key"] = f"{installationFolder}/manualcerts/google.com.key"
            certPaths["pem"] = f"{installationFolder}/manualcerts/google.com.pem"
            certPaths["caKey"] = f"{installationFolder}/manualcerts/myCA.key"
            certPaths["caPem"] = f"{installationFolder}/manualcerts/myCA.pem"
            break
        elif googleKey and googlePem and (not caKey or not caPem): # If SSL certs are present but CA's aren't
            if config["bypassCA"]: # If the user has bypassCA set, we'll bypass the need for CA
                colorprint("CA bypass is active. Using manual certificates for Icarus Lite.", "green")
                colorprint("WARNING: When using CA bypass, certificate verification and regeneration will be unavailable.", "blue")
                certPaths["key"] = f"{installationFolder}/manualcerts/google.com.key"
                certPaths["pem"] = f"{installationFolder}/manualcerts/google.com.pem"
                noSupport = True
                break
            elif not messageDisplayed[1]:
                colorprint("! IMPORTANT !", "red")
                colorprint("Manual certificates found, but CA's are missing. If you would like to continue without CA's, please create an empty file named 'bypassCA.txt'.", "blue")
                messageDisplayed[1] = True
        # If the user doesn't have certs in manualcerts on first check, prompt them to put them in.
        if messageDisplayed[0] == False:
            colorprint(f"""Please manually download the following certificates:
                       - google.com.key 
                       - google.com.pem
                       - myCA.key
                       - myCA.pem
                       Place them in:
                       {installationFolder}/manualcerts/
                       Waiting for certificates..."""
                       , "blue")
            messageDisplayed[0] = True # Ensure the message isn't displayed every loop iteration
        # small delay
        time.sleep(1)

# Below is a function that clears the console
clear = lambda: os.system("cls") if os.name == "nt" else os.system("clear")

# Custom function to print text with color to enhance user experience while reducing dependies (such as Colorama) that are needed
def colorprint(text, color):
    # If noSupport is True, we'll append [NS] to the beginning of every printed line.
    if color == "blue":
        print(f"\033[34m{text if not noSupport else '[NS] ' + text}\033[0m")
    elif color == "green":
        print(f"\033[32m{text if not noSupport else '[NS] ' + text}\033[0m")
    elif color == "red":
        print(f"\033[31m{text if not noSupport else '[NS] ' + text}\033[0m")

def generateCerts():
    # Load CA certificate and key using cryptography
    with open(certPaths["caPem"], "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(certPaths["caKey"], "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)
    # Verify that the CA certificate and key match by comparing their public keys
    ca_cert_pub = ca_cert.public_key()
    ca_key_pub = ca_key.public_key()
    ca_cert_pub_bytes = ca_cert_pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    ca_key_pub_bytes = ca_key_pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    if ca_cert_pub_bytes != ca_key_pub_bytes:
        return -1  # -1 return code means CA's don't match
    # Generate a new private key for google.com
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    # Build subject for the new certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "PRIVATE"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "PRIVATE"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Success!"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Success"),
        x509.NameAttribute(NameOID.COMMON_NAME, "*.google.com"),
    ])
    # Set the issuer from the CA certificate's subject
    issuer = ca_cert.subject
    # Build the certificate with timezone-aware validity dates
    cert_builder = x509.CertificateBuilder()\
        .subject_name(subject)\
        .issuer_name(issuer)\
        .public_key(key.public_key())\
        .serial_number(1000)\
        .not_valid_before(datetime.now(timezone.utc))\
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    # Create AuthorityKeyIdentifier extension using the CA's public key info
    ca_subject_key_identifier = x509.SubjectKeyIdentifier.from_public_key(ca_cert_pub)
    authority_key_identifier = x509.AuthorityKeyIdentifier(
        key_identifier=ca_subject_key_identifier.digest,
        authority_cert_issuer=[x509.DirectoryName(issuer)],
        authority_cert_serial_number=ca_cert.serial_number
    )
    cert_builder = cert_builder.add_extension(authority_key_identifier, critical=False)
    # Add BasicConstraints extension (indicating this cert is not a CA)
    cert_builder = cert_builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True
    )
    # Add KeyUsage extension
    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=True,
            key_encipherment=True,
            data_encipherment=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True
    )
    # Add SubjectAlternativeName extension for the wildcard domain
    cert_builder = cert_builder.add_extension(
        x509.SubjectAlternativeName([x509.DNSName("*.google.com")]),
        critical=False
    )
    # Sign the certificate using the CA's private key
    cert = cert_builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
    # Save the new certificate and key
    try:
        with open(f"{installationFolder}/manualcerts/google.com.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(f"{installationFolder}/manualcerts/google.com.key", "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
    except Exception:
        return -2  # -2 return code means error saving new certificates
    return 0  # 0 return code means success

if os.name == "nt": # If on Windows
    os.system(f"title Icarus Lite") # Set window title
else:
    sys.stdout.write(f"\033]0;Icarus Lite\007") # Set window title
    sys.stdout.flush()
colorprint(f"Icarus Lite v{version}", "blue")
colorprint("Written by cosmicdevv", "blue")
"""
CONFIGURATION LOADER
"""
if os.path.exists(f"{installationFolder}/config.json"):
    colorprint("Reading Icarus Lite config...", "blue")
    with open(f"{installationFolder}/config.json", "r+") as configFile: # load config bullshit
        try:
            newConfig = config.copy()
            configFileJson = json.loads(configFile.read())
            for cfg_key, cfg_val in configFileJson.items(): # Iterate through every config key and value in the config.json file
                if cfg_key in config: # If the key is a key present in the default config, continue
                    newConfig[cfg_key] = cfg_val # Set the newConfig value of the key to the value (i did not explain that shit good)
            if newConfig.keys() > configFileJson.keys(): # If they have a different amount of values
                colorprint("Updating config.json file with latest configuration values...", "green")
                configFile.seek(0)
                configFile.truncate()
                configFile.write(json.dumps(newConfig)) # Set the config file to recognized config
                colorprint("config.json file updated.")
            config = newConfig.copy()
            colorprint("Icarus Lite configuration loaded.", "green")
        except:
            colorprint("Error reading configuration! If manually edited, please check syntax. Using default configuration.", "red")
# If the config.json file doesn't exist, we don't have to create it here because it gets created later in the code.
"""
AUTO-UPDATER
"""
colorprint("Checking for updates...", "blue")
checked = True
try:
    response = requests.get(latestVersionUrl).text
except Exception as e:
    checked = False # Ensure it doesn't say "No updates found" later, and only prints that it couldn't check for updates
    response = version # Set the latest version to the current version.
    colorprint("Could not check for latest updates, please check any firewalls or network restrictions. Icarus Lite will continue running normally.", "red")
v = tuple(map(int, version.split('.'))) # Convert current script version to a tuple
lv = tuple(map(int, response.split('.'))) # Convert latest version to a tuple
# Check if latest version is more than current version
if lv > v:
    colorprint(f"New script update found! Latest version: v{response}", "green")
    if config["autoUpdate"]:
        colorprint("autoUpdate flag is set to true in Icarus Lite local configuration. Updating...", "green")
        choice = True
    else:
        colorprint("Do you want to automatically update? (Y/N)", "blue")
        while True:
            choice = input().lower()
            if choice in ["y", "yes"]:
                choice = True
                break
            elif choice in ["n", "no"]: # They chose not to update
                colorprint("Icarus Lite will not update and will run on installed version.", "blue")
                colorprint("! IMPORANT !", "red")
                colorprint("Support will not be given to users running outdated versions.", "red")
                noSupport = True
                break
    if choice == True: # If user selected to update or auto-update is set
        if getattr(sys, "frozen", False): # Running on exe
            colorprint("! IMPORTANT !", "red")
            colorprint("Icarus Lite cannot auto-update when ran as a compiled file (such as an exe). Please refer to the GitHub repository to download latest precompiled Icarus Lite versions.", "blue")
            colorprint("Support will not be given to users running outdated versions.", "red")
            noSupport = True
        else:
            newFile = requests.get(scriptUrl)
            # If the retrieval was successful
            if newFile.status_code == 200:
                # Overwrite the script with the latest script version
                with open(sys.argv[0], "wb") as f:
                    f.write(newFile.content)
                colorprint("Script updated successfully! Restarting...", "green")
                # Restart the script
                if os.name == "nt": # If on Windows
                    subprocess.Popen([sys.executable] + sys.argv)
                    sys.exit()
                else: # If on any other OS
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            else: # Script wasn't downloaded successfully
                print("Failed to download latest update.", response.status_code)
                colorprint("! IMPORANT !", "red")
                colorprint("Support will not be given to users running outdated versions.", "red")
                noSupport = True
else:
    if checked: # If the latest version was successfully retrieved
        colorprint(f"No updates found. Latest version: v{version}", "green")
"""
FILE STRUCTURE AUTOMATIC SETUP
"""
colorprint("Checking installation...", "blue")
# Check if the Icarus folder exists
firstTime = False
if not os.path.exists(installationFolder) or not os.path.exists(f"{installationFolder}/autocerts") or not os.path.exists(f"{installationFolder}/manualcerts") or not os.path.exists(f"{installationFolder}/config.json"):
    firstTime = True
    colorprint("! WARNING !\nIcarus Lite is not set up in the local directory. Do you want to automatically set up? (Y/N)", "blue")
    # Ask the user if they want to create the Icarus folder, loop to ensure valid input
    while True:
        choice = input().lower()
        if choice in ["y", "yes"]:
            break
        elif choice in ["n", "no"]:
            colorprint("Icarus Lite will not set up due to user choice.", "red")
            sys.exit()
    # If they selected yes, create necessary folders
    colorprint("Creating install folder...", "blue")
    os.makedirs(installationFolder, exist_ok=True)
    colorprint("Creating certificate folder...", "blue")
    os.makedirs(f"{installationFolder}/autocerts", exist_ok=True)
    colorprint("Creating manual certificate folder...", "blue")
    os.makedirs(f"{installationFolder}/manualcerts", exist_ok=True)
    with open(f"{installationFolder}/config.json", "w") as configFile:
        configFile.write(json.dumps(config)) # Write default configuration
else:
    colorprint("Icarus Lite installation is valid.", "green")
if not config["disableDelays"]: # If disableDelays is false
    colorprint("Continuing in 5 seconds...", "green")
    time.sleep(5)
clear()
"""
CERTIFICATE CONFIGURATION
"""
showOptions = True
if config["autoCertificateMode"] in [1, 2]: # If autoCertificateMode config is 1 or 2
    colorprint(f"autoCertificateMode flag is set to '{config['autoCertificateMode']}' in Icarus Lite local configuration.", "green")
    choice = config["autoCertificateMode"]
    showOptions = False # Make sure options aren't shown since a recognized config value is applied
elif config["autoCertificateMode"] != 0: # If autoCertificateMode is set, but not to 1 or 2
    colorprint(f"WARNING: autoCertificateMode config is set, but to an unrecognized value of '{config['autoCertificateMode']}'. The configuration value will be ignored.", "red")
if showOptions:
    # Give the user the option to use manual certs or automatically downloaded certs
    colorprint("CERTIFICATE OPTIONS:\n\n1. Automatically download latest certificates [RECOMMENDED]\n2. Use manual (local) certificates [DEBUG ONLY]\n\nEnter 1/2 for choice.", "blue")
    # Let the user choose
    while True:
        choice = input().lower()
        if choice in ["1", "one"]:
            choice = 1 # Make sure choice is an integer
            break
        if choice in ["2", "two"]:
            choice = 2 # Make sure choice is an integer
            break
if choice == 1: # If they selected to automatically download certificates
    colorprint("Downloading latest Icarus SSL certificates...", "blue")
    success = True # If a download fails, this gets set to false
    # Loop through all the necessary SSL certificates, where their filename is the key and the download url is the value
    for sslCert in sslCerts:
        try:
            # Try to download the certificate from the url and place it in the autocerts folder
            response = requests.get(sslCerts[sslCert])
            with open(f"{installationFolder}/autocerts/{sslCert}", 'wb') as file:
                file.write(response.content)
            if firstTime:
                # Create a backup copy of the certificate in the manualcerts folder
                shutil.copy(f"{installationFolder}/autocerts/{sslCert}", f"{installationFolder}/manualcerts/{sslCert}")
            colorprint(f"Latest '{sslCert}' downloaded. (from github)", "green")
        except Exception as e:
            # If the download fails
            success = False
            colorprint(f"'{sslCert}' failed to download.", "red")
    # If not all downloads were successful, run this
    if not success:
        colorprint("One or more certificates could not be downloaded. Icarus Lite is unable to run from auto-downloaded certificates.", "red")
        handleManualCertificates()
    else:
        # If all downloads were successful, we'll use the downloaded certs
        certPaths["key"] = f"{installationFolder}/autocerts/google.com.key"
        certPaths["pem"] = f"{installationFolder}/autocerts/google.com.pem"
        certPaths["caKey"] = f"{installationFolder}/autocerts/myCA.key"
        certPaths["caPem"] = f"{installationFolder}/autocerts/myCA.pem"
else: # If they selected to use manual certificates
    handleManualCertificates()
if certPaths["caKey"] != None and certPaths["caPem"] != None:
    colorprint("Validating certificates...", "blue")
    with open(certPaths["caPem"], "rb") as f: # Load CA
        ca = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())
    with open(certPaths["pem"], "rb") as f: # Load SSL certificate
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())
    # Verify if the issuer of the certificate matches the CA
    isInvalid = cert.get_issuer().hash() != ca.get_subject().hash()
    # Check if the certificate is expired
    isExpired = datetime.strptime(cert.get_notAfter().decode("utf-8"), "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    if isInvalid or isExpired:
        colorprint("Certificates are invalid and Icarus Lite will not work as expected.", "red")
        colorprint("Do you want to build new certificates? (Y/N)", "blue")
        while True:
            choice = input().lower()
            if choice in ["y", "yes"]:
                certs = generateCerts()
                if certs == -1: # -1 means CA's don't match
                    colorprint("Could not build new certificates because the CA key and pem do not match.")
                if certs == -2: # -2 means failed to save certs
                    colorprint("Could not save new certificates.")
                if certs != 0: # If the generation wasn't successful
                    colorprint("! IMPORTANT !", "red")
                    colorprint("Icarus Lite could not build new certificates and may not work as expected.", "blue")
                    colorprint("YOU WILL NOT RECIEVE SUPPORT WHILE RUNNING WITH INVALID CERTS!", "blue")
                    noSupport = True
                else:
                    colorprint("Successfully regenerated SSL certificates.", "green")
                    certPaths["key"] = f"{installationFolder}/manualcerts/google.com.key"
                    certPaths["pem"] = f"{installationFolder}/manualcerts/google.com.pem"
                break
            if choice in ["n", "no"]:
                colorprint("! IMPORTANT !", "red")
                colorprint("Icarus Lite may not work as expected because the certificates are not correct and you have chosen not to regenerate the certificates.", "blue")
                colorprint("YOU WILL NOT RECIEVE SUPPORT WHILE RUNNING WITH INVALID CERTS!", "blue")
                noSupport = True
                break
    else:
        colorprint("Certificates are valid!", "green")
else:
    colorprint("WARNING: CA bypass is active and certificates have not been validated.", "blue")
    colorprint("SUPPORT WILL NOT BE OFFERED FOR CERTIFICATES THAT CAN NOT BE VALIDATED!", "red")
if not config["disableDelays"]: # If disableDelays is false
    colorprint("Continuing in 5 seconds...", "green")
    time.sleep(5)
clear()

"""
PROXY SERVER STARTUP LOGIC
"""

port = 8126
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_socket.bind(("0.0.0.0", port))
proxy_socket.listen(100)

# Get the local IP for the user
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 1))
local_ip = s.getsockname()[0]
s.close()

# aaaaaaaaaaaaaaaaaaaaaa
colorprint(f"Icarus Lite is running on: {local_ip}:{port}", "green")
colorprint("Refer to the Icarus Lite GitHub repository for usage information.", "blue")
colorprint("Requests will be logged below.", "blue")
print("\n\n")
while True:
    try:
        client_socket, client_address = proxy_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.daemon = True
        client_thread.start()
    except KeyboardInterrupt:
        print("Icarus Lite is shutting down...")
        proxy_socket.close()
        break
    except Exception as e:
        print(f"Error accepting connection: {e}")
proxy_socket.close()