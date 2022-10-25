<p align="center"><img src="https://media.discordapp.net/attachments/856404208445292545/984730065315201054/khonshu.png"></p>

<h2 align="center">
<code>khonshu</code> 🗿</h2>
 
This project is a collection of tools that may be the barebone of a malicious projects.

## Index

- Information Extraction

    These **only** work on Windows. However, this does not, in any way, mean that implementations for other OS cannot be made.

    - [Discord Token](./khonshu/webauth/discord/tokencore.py)
        - [Verifier](./khonshu/webauth/discord/verifier.py)
    - [Browser Storage](./khonshu/webauth/browser.py)        
        - [Cookies](./khonshu/webauth/browser.py)
        - [Credentials](./khonshu/webauth/browser.py)
        - [History](./khonshu/webauth/browser.py)
    - [Device](./khonshu/system/memproc.py)
- System
    - [Elevation / Privileged Access](./khonshu/elevation)
        - [Windows](./khonshu/elevation/windows.py)
        - [Systems that use `sudo`](./khonshu/elevation/sudo.py)

        > **Note:** These are **not** exploits, they will require the user to give some level of consent.


## Utility

The utilities in thie project may be used by non-malicious projects to gain what could be a protected information within in a system. This may include some of the following:

- [Cloudflare bypass using user's cookie.](./cloudflare_bypass.py)
- Transfer of browser storage from old to new browser.
- Extracting credentials for using in own or trusted projects.
- Remotely extracting information from a system.

## The main point

This project mainly shows you how simple it is to gain critical information from a system, even without privileged access.

This means that simply not handing `sudo` or Administrator privileges to a malicious script does not protect your device. A simple accidental run can export nearly all information available.

The ultimate method of protection is common sense.
