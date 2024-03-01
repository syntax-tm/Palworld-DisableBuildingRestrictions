#include "pch.h"
#include <windows.h>
#include <fstream>
#include <vector>
#include <sstream>
#include <iomanip>
#include <wincrypt.h>
#include <codecvt>
#include <algorithm>

struct MemoryModification
{
	LPVOID address;
	BYTE* bytes;
	SIZE_T size;
};

void Log(const std::string& message)
{
	std::ofstream logFile("log.txt", std::ios::app);
	if (logFile.is_open())
	{
		logFile << message << std::endl;
		logFile.close();
	}
}

LPVOID GetModuleBaseAddress()
{
	HMODULE hModule = GetModuleHandle(nullptr);

	if (hModule != nullptr)
	{
		Log("Module handle obtained.");

		auto baseAddress = hModule;

		char buffer[256];
		sprintf_s(buffer, "Base address of the module: 0x%p", baseAddress);
		Log(buffer);

		return baseAddress;
	}
	Log("Error obtaining module handle.");

	return nullptr;
}

bool ModifyMemory(const std::vector<MemoryModification>& modifications)
{
	Log("Applying Patches...");

	LPVOID moduleBaseAddress = GetModuleBaseAddress();
	if (moduleBaseAddress != nullptr)
	{
		for (const auto& modification : modifications)
		{
			auto addressToModify = (LPVOID)((DWORD_PTR)moduleBaseAddress + (DWORD_PTR)modification.address);

			char buffer[256];
			sprintf_s(buffer, "Modifying address: 0x%p", addressToModify);
			Log(buffer);

			if (!WriteProcessMemory(GetCurrentProcess(), addressToModify, modification.bytes, modification.size,
			                        nullptr))
			{
				Log("Error modifying address.");
				return false;
			}
			Log("Address modified successfully.");
		}
		for (const auto& modification : modifications)
		{
			delete[] modification.bytes;
		}
	}
	else
	{
		Log("Error getting module base address.");
		return false;
	}

	return true;
}

void LogProcessInfo()
{
	DWORD processId = GetCurrentProcessId();

	std::ofstream logFile("log.txt", std::ios::app);
	if (logFile.is_open())
	{
		logFile << "Process ID Found: " << processId << std::endl;
		logFile.close();
	}
}

void ForceCloseProcess()
{
	Log("Forcefully closing the process...");
	TerminateProcess(GetCurrentProcess(), 1);
}

void DisplayMessageBox(const std::wstring& message)
{
	MessageBox(nullptr, message.c_str(), L"Error", MB_ICONERROR | MB_OK);
}

std::wstring CalculateFileMD5(const std::wstring& filePath)
{
	std::wstring md5Hash;

	HANDLE hFile = CreateFile(filePath.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
	                          FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
	if (hFile == INVALID_HANDLE_VALUE)
	{
		return md5Hash;
	}

	HCRYPTPROV hProv;
	if (!CryptAcquireContext(&hProv, nullptr, nullptr, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT))
	{
		CloseHandle(hFile);
		return md5Hash;
	}

	HCRYPTHASH hHash;
	if (!CryptCreateHash(hProv, CALG_MD5, 0, 0, &hHash))
	{
		CloseHandle(hFile);
		CryptReleaseContext(hProv, 0);
		return md5Hash;
	}

	constexpr DWORD bufferSize = 8192;
	BYTE buffer[bufferSize];
	DWORD bytesRead;

	while (ReadFile(hFile, buffer, bufferSize, &bytesRead, nullptr) && bytesRead > 0)
	{
		CryptHashData(hHash, buffer, bytesRead, 0);
	}

	DWORD hashSize = 16;
	BYTE hash[16];
	if (CryptGetHashParam(hHash, HP_HASHVAL, hash, &hashSize, 0))
	{
		std::wstringstream ss;
		ss << std::hex << std::uppercase << std::setfill(L'0');
		for (DWORD i = 0; i < hashSize; i++)
		{
			ss << std::setw(2) << static_cast<unsigned int>(hash[i]);
		}
		md5Hash = ss.str();
	}

	CryptDestroyHash(hHash);
	CryptReleaseContext(hProv, 0);
	CloseHandle(hFile);

	return md5Hash;
}

std::wstring GetExecutablePath()
{
	wchar_t buffer[MAX_PATH];
	GetModuleFileName(nullptr, buffer, MAX_PATH);
	return buffer;
}

void DeleteLogFile()
{
	if (remove("log.txt") == 0)
	{
		Log("Old Log file deleted.");
	}
	else
	{
		Log("Error deleting Old log file.");
	}
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
{
	std::vector<MemoryModification> modifications;
	std::wstring expectedMD5;

	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:
		Sleep(1000);
		DeleteLogFile();
		Log("PalPatcher Initializing.");

		std::wstring executablePath = GetExecutablePath();
		std::wstring executableName = executablePath.substr(executablePath.find_last_of(L"\\") + 1);
		std::transform(executableName.begin(), executableName.end(), executableName.begin(), towlower);

		if (executableName.find(L"palworld") != std::wstring::npos)
		{
			// PALWORLD
			Log("Found palworld!");
			modifications = {
				{(LPVOID)0x2980845, new BYTE[2]{0xEB, 0x15}, 2}, // Allow building close to palbox
				{(LPVOID)0x2975D5E, new BYTE[6]{0x90, 0x90, 0x90, 0x90, 0x90, 0x90}, 6}, // Building in mid air
				{(LPVOID)0x2A59ED2, new BYTE[2]{0x90, 0x90}, 2}, // Overlapping bases
				{(LPVOID)0x2A59DEF, new BYTE[2]{0xEB, 0x07}, 2}, // Disable world collision
				{(LPVOID)0x2975DEC, new BYTE[2]{0xEB, 0x0E}, 2}, // Allow building on water
				{(LPVOID)0x2963F7B, new BYTE[2]{0x90, 0x90}, 2}, // Support Restriction Remove
				{(LPVOID)0x2AA4AEF, new BYTE[2]{0x90, 0x90}, 2} // Support Restriction Remove2
			};
			expectedMD5 = L"215F91EEB43BA28FE4C3EA648EE0ECE9";
		}
		else if (executableName.find(L"palserver") != std::wstring::npos)
		{
			// PALSERVER
			Log("Found palserver!");
			modifications = {
				{(LPVOID)0x295F5D5, new BYTE[2]{0xEB, 0x15}, 2}, // Allow building close to palbox
				{(LPVOID)0x2954C23, new BYTE[6]{0x90, 0x90, 0x90, 0x90, 0x90, 0x90}, 6}, // Building in mid air
				{(LPVOID)0x2A35512, new BYTE[2]{0x90, 0x90}, 2}, // Overlapping bases
				{(LPVOID)0x2A3542F, new BYTE[2]{0xEB, 0x07}, 2}, // Disable world collision
				{(LPVOID)0x2954CB3, new BYTE[2]{0xEB, 0x0E}, 2}, // Allow building on water
				{(LPVOID)0x2A7FD9F, new BYTE[2]{0x90, 0x90}, 2} // Support Restriction Remove2
			};
			expectedMD5 = L"FD863E5DCB896C05F7B0B4EDAAEF312A";
		}
		else
		{
			Log("Did not find palserver or palworld!");
			DisplayMessageBox(
				L"Executable is not palserver or palworld.\nThis patcher is meant for either of those 2 executables.");
			break;
		}

		std::wstring actualMD5 = CalculateFileMD5(executablePath);
		std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;

		Log("EXE Path: " + converter.to_bytes(executablePath));
		Log("MD5 of current EXE: " + converter.to_bytes(actualMD5));
		Log("MD5 of supported EXE: " + converter.to_bytes(expectedMD5));

		if (actualMD5 != expectedMD5)
		{
			DisplayMessageBox(
				L"Invalid executable version. The game will not launch to protect your base.\nPlease see the GitHub Instructions.txt or the Nexusmods mod page for more info.");

			ForceCloseProcess();
			return FALSE;
		}

		if (!ModifyMemory(modifications))
		{
			DisplayMessageBox(
				L"Failed to apply modifications. The game has been forcefully closed to protect your base.\nPlease see the GitHub Instructions.txt or the Nexusmods mod page for more info.");
			ForceCloseProcess();
			return FALSE;
		}

		LogProcessInfo();
		break;
	}

	return TRUE;
}
