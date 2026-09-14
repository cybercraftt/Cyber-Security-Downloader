# 🛡️ Cyber Security Downloader

**Cyber Security Downloader** is a portable Windows downloader that brings several popular security utilities together in one simple and convenient interface.

The application allows you to quickly download the latest versions of **Dr.Web CureIt!**, **AdwCleaner**, **MinerSearch**, and other supported utilities, check the status of locally stored files, download updates, and launch downloaded tools directly from the application.

The project is written in **Python + CustomTkinter**, is open source, and does not require installation.

## ✨ Features

* 🦠 **Multiple security utilities** in one application
* 🔄 **Update checking** before downloading
* 📊 **Local and remote file size comparison**
* ⚡ **Download speed and progress display**
* ⏱️ **Estimated remaining download time**
* 🔐 **HTTPS downloads** with file validation
* 🛡️ `.exe` validation using the Windows `MZ` header
* #️⃣ **SHA-256 hash calculation** after downloading
* ❌ **Cancel downloads** at any time
* ▶️ **Launch downloaded utilities** directly from the application
* 📁 Choose a custom download directory
* 📦 Fully portable - no installation required
* 🔊 Sound notification when a download is completed
* 🌍 Multi-language interface
* 🌙 Modern dark interface built with CustomTkinter
* 💾 Persistent application settings

## 🧰 Supported Utilities

### Dr.Web CureIt!

A standalone antivirus scanner designed to check Windows systems for malware and other threats.

### AdwCleaner

A utility for detecting and removing Adware, PUPs, unwanted browser components, and related software.

### MinerSearch

A utility for detecting and removing hidden cryptocurrency miners.

> The list of supported utilities may be expanded in future releases.

## 🔐 Secure Download Process

Cyber Security Downloader is **not an antivirus** and does not replace dedicated security software. Its purpose is to provide a convenient way to obtain and launch supported security utilities.

During the download process, the application:

1. Connects to the server using HTTPS.
2. Retrieves the remote file size.
3. Downloads the file into a temporary `.tmp` file.
4. Displays download progress, speed, and estimated remaining time.
5. Checks the downloaded file size.
6. Validates Windows `.exe` files by checking for the `MZ` header.
7. Calculates the SHA-256 hash.
8. Moves the verified file to its final location.

This helps prevent situations where an error page, incomplete download, or invalid file is saved as an executable.

## 📦 Portable

Cyber Security Downloader does not require installation.

You can use:

* a ready-to-use `.exe` build;
* the Python source code;
* the `Downloads` folder located next to the application;
* any custom directory selected by the user.

Application settings are stored in `settings.json`.

## 🌍 Languages

The interface currently supports:

🇷🇺 Russian
🇺🇸 English
🇪🇸 Spanish
🇩🇪 German
🇫🇷 French
🇨🇳 Chinese
🇵🇹 Portuguese
🇯🇵 Japanese

## 🖥️ System Requirements

**Operating system:**

* Windows 10
* Windows 11

For running from source:

* Python 3.x
* CustomTkinter
* Pillow - if required by the corresponding functionality
* Internet connection

## 🚀 Running from Source

### 1. Clone the repository

```bash
git clone https://github.com/cybercraftt/Cyber-Security-Downloader.git
cd Cyber-Security-Downloader
```

### 2. Install dependencies

```bash
pip install customtkinter
```

If Pillow is required:

```bash
pip install pillow
```

### 3. Run the application

```bash
python "Cyber Security Downloader.py"
```

## 🏗️ Technologies

The project is built with:

* **Python 3**
* **CustomTkinter** - graphical user interface
* **urllib** - network communication and file downloads
* **threading** - background download operations
* **hashlib** - SHA-256 calculation
* **zipfile** - archive handling
* **PyInstaller** - portable `.exe` builds

## 📁 Project Structure

```text
Cyber-Security-Downloader/
│
├── Cyber Security Downloader.py
├── icon.ico
├── alert.wav
├── README.md
├── LICENSE
│
└── Downloads/
    ├── cureit.exe
    ├── adwcleaner.exe
    └── ...
```

## ⚠️ Important

Cyber Security Downloader **is not an antivirus** and does not replace dedicated security software.

The application is a downloader and launcher for supported third-party security utilities.

Always make sure that downloaded executable files come from trusted and official sources.

The portable `.exe` build may trigger a Windows SmartScreen or antivirus warning if the executable does not have a valid digital signature. This can happen with unsigned PyInstaller applications.

If you are unsure about the executable, you can:

1. Review the project source code.
2. Download the application from the official repository.
3. Build the application yourself.
4. Scan the resulting file with Windows Security or another trusted security solution.

## 📜 License

This project is released under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

## 🧡 Support the Project

If Cyber Security Downloader is useful to you and you would like to support its development:

**Boosty:**
https://boosty.to/cyber_craft

Support is completely voluntary and helps with the development of new utilities and improvements to existing projects.

## 🌐 Cyber Craft

Follow the project and discover more tools:

* 📺 **YouTube:** https://www.youtube.com/channel/UCcGfKjP4XdfkLokNgVOIAyA
* 💬 **Telegram:** https://t.me/CyberCraftLab
* 🧡 **Boosty:** https://boosty.to/cyber_craft

---

<p align="center">

**Made with 🖤 by Cyber Craft**

</p>
