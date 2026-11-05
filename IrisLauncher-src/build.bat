@echo off
rem Membangun ulang IrisLauncher.exe di Windows tanpa memasang apa pun (memakai csc.exe bawaan .NET Framework).
cd /d "%~dp0"
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
"%CSC%" /nologo /target:winexe /optimize+ /debug- /out:IrisLauncher.exe /win32icon:iris.ico /win32manifest:app.manifest ^
  /r:System.Windows.Forms.dll /r:System.Drawing.dll ^
  /resource:iris-start.ps1,iris-start.ps1 /resource:iris-stop.ps1,iris-stop.ps1 ^
  /resource:iris-hermes.ps1,iris-hermes.ps1 /resource:iris-doctor.ps1,iris-doctor.ps1 /resource:iris-service.ps1,iris-service.ps1 ^
  /resource:logo.png,logo.png /resource:iris.ico,iris.ico ^
  IrisLauncher.cs
if errorlevel 1 (echo GAGAL membangun. & pause) else (echo Selesai: IrisLauncher.exe & certutil -hashfile IrisLauncher.exe SHA256 & timeout /t 8)
