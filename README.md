## Palworld-DisableBuildingRestrictions

- [Palworld-DisableBuildingRestrictions](#palworld-disablebuildingrestrictions)
- [DLL Version](#dll-version)
  - [Prerequisites](#prerequisites)
  - [Installing](#installing)
  - [Notes](#notes)
  - [Uninstalling](#uninstalling)
- [GUI Version](#gui-version)
  - [Installing](#installing-1)
  - [Usage](#usage)
    - [Command Line](#command-line)
- [Python Command Line Version](#python-command-line-version)
  - [Prerequisites](#prerequisites-1)
  - [Installing](#installing-2)
  - [Options](#options)
    - [Permanent Method](#permanent-method)
    - [Temporary Method](#temporary-method)
  - [Usage](#usage-1)
    - [Command Line](#command-line-1)
- [FAQs](#faqs)

## DLL Version

### Prerequisites

- An unmodified game or server executable
  - If you previously used the patcher and chose the permanent option, you must restore the original `.exe`.

> [!NOTE]
> If you are unable to restore the original `.exe` using the patcher, you can restore the original file using the `Verify integrity of game files` option in Steam

### Installing

1. Download [t4bby's DLL Loader](https://www.nexusmods.com/palworld/mods/372)
2. Download `PalPatcher.dll`
3. Copy `PalPatcher.dll` into the mod loader's plugins directory

### Notes

`PalPatcher.dll` has 2 safety checks to protect your base.

1. Checks the executable version to make sure it is supported
2. Verifies the patch was successful

If either one fails the game or server will be forcibly closed and a message will be displayed informing you what happened.

> [!TIP]
> If this happens you should first retry since intermittent failures can occur. If it continues to fail it's most likely because the game has been updated and you should wait for an update to `PalPatcher`.

> [!CAUTION]
> If you cant wait for an update and decide to remove PalPatcher then anything you placed with not enough support will get destroyed.

### Uninstalling

To uninstall `PalPatcher` simply remove `PalPatcher.dll`.

## GUI Version

### Installing

1. Download `BuildPatcher.exe` and `BuildPatcher.ini`
2. Open `BuildPatcher.ini` and set `palworld_root` and/or `palserver_root` to your game and/or server's root folder
3. Remove any unwanted mods/patches in the ini
4. Run `BuildPatcher.exe` and choose your method to modify the game and/or server
   - For a **temporary patch**, you will need to run the patcher every time before playing
   - For a **permanent patch**, you will only need to run the patcher once

### Usage

#### Command Line

This version also supports command line arguments. When passed, the argument `Temporary_Server` will perform a temporary patch on the confiugred (via the `.ini`) server executable.

```ps1
BuildPatcher.exe Temporary_Server
```

## Python Command Line Version

### Prerequisites

- [Python](https://www.python.org/)

### Installing

1. Download `BuildPatcher.py` and `BuildPatcher.ini`
2. Open `BuildPatcher.ini` and set `palworld_root` and/or `palserver_root` to your game and/or server's root folder
3. Open a command line
   - Windows users can right-click the **Start Menu** and select **Terminal (Admin)** (or **Powershell (Admin)** depending on which version of Windows you are using)
4. Run `BuildPatcher.py`
5. Select an option when presented

### Options

#### Permanent Method

- Can use Steam to launch the game normally
- No safety measures for preserving bases
  - If the game is updated and started without first being re-patched, your bases could be potentially be destroyed if they lack proper support

#### Temporary Method

- Requires running the game through the patcher every time
- Has the benefit of increased safety since game version and patching is confirmed before starting the game
  - A warning is shown whenever the patching fails
  - Ignoring the warning can potentially cause your bases to be destroyed if they lack proper support

### Usage

#### Command Line

This version accepts command line arguments for automation. For example, passing `1` when starting the script will auto-select option 1.

```ps1
python BuildPatcher.py 1
```

## FAQs

1. **Wnat's the difference between this and CactusPi3's files?**

   - Cactus' version edits the program after it's loaded into memory. This version modifies the executable file so that when it's loaded into memory it's always patched.

2. **Does this require an installation?**

   - Any of the options can be run from anywhere and do not require installation. The `.ini` file must be in the same directory as the the `.py` or `.exe` file depending on which one you're using. The `.ini` file should also include the root directory of the game and/or server.

3. **Which option is best?**

   - It is **HIGHLY** recommended that you use the DLL version as it has the best safegaurds in place.

4. **Do I need CheatEngine?**

   - No. If you want to use CheatEngine, you can download the `.ct` file in the `src/cheatengine/` folder.

5. **What do I put for the server path in the .ini file?**

   - If you **don't** have the dedicated server installed, you can ignore the server functions and leave `palserver_root` empty in the `.ini` file.

6. **How do I open the .py file?**

   - You didn't select the option to add Python to the PATH when you installed Python. Either look up a guide on how to do it manually, or reinstall Python with that option checked.
