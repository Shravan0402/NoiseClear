"""Create Desktop shortcut and Start Menu entry for NoiseClear."""

import os
import sys
import subprocess


def create_shortcut(shortcut_path, target_path, icon_path, description, working_dir):
    """Create a Windows .lnk shortcut using PowerShell."""
    # Normalize all paths to use backslashes for Windows COM
    shortcut_path = os.path.normpath(shortcut_path)
    target_path = os.path.normpath(target_path)
    icon_path = os.path.normpath(icon_path)
    working_dir = os.path.normpath(working_dir)

    ps_script = (
        '$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut(\'{shortcut_path}\'); '
        f'$Shortcut.TargetPath = \'{target_path}\'; '
        f'$Shortcut.WorkingDirectory = \'{working_dir}\'; '
        f'$Shortcut.IconLocation = \'{icon_path}\'; '
        f'$Shortcut.Description = \'{description}\'; '
        '$Shortcut.Save()'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  PowerShell error: {result.stderr.strip()}")
    return result.returncode == 0


def main():
    # Paths - use os.path.normpath to guarantee backslashes
    project_dir = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.normpath(os.path.join(project_dir, "dist", "NoiseClear"))
    exe_path = os.path.normpath(os.path.join(dist_dir, "NoiseClear.exe"))
    icon_path = os.path.normpath(os.path.join(dist_dir, "icon.ico"))

    # Fallback icon
    if not os.path.exists(icon_path):
        icon_path = os.path.normpath(os.path.join(project_dir, "icon.ico"))
    if not os.path.exists(icon_path):
        icon_path = exe_path

    if not os.path.exists(exe_path):
        print(f"ERROR: NoiseClear.exe not found at {exe_path}")
        print("Run PyInstaller build first!")
        sys.exit(1)

    print(f"Executable found: {exe_path}")
    print(f"Icon: {icon_path}")
    print()

    description = "NoiseClear - Real-time Noise Cancellation"

    # 1. Desktop Shortcut
    desktop = os.path.normpath(os.path.join(os.path.expanduser("~"), "Desktop"))
    if not os.path.isdir(desktop):
        # Try OneDrive Desktop
        desktop = os.path.normpath(os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"))
    if not os.path.isdir(desktop):
        # Last resort: query via PowerShell
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[Environment]::GetFolderPath('Desktop')"],
            capture_output=True, text=True
        )
        desktop = result.stdout.strip()

    print(f"Desktop folder: {desktop}")
    desktop_shortcut = os.path.normpath(os.path.join(desktop, "NoiseClear.lnk"))

    if create_shortcut(desktop_shortcut, exe_path, icon_path, description, dist_dir):
        print(f"  Desktop shortcut created: {desktop_shortcut}")
    else:
        print("  Failed to create desktop shortcut")

    # 2. Start Menu Shortcut
    start_menu = os.path.normpath(os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs"
    ))
    start_menu_dir = os.path.normpath(os.path.join(start_menu, "NoiseClear"))
    os.makedirs(start_menu_dir, exist_ok=True)
    start_shortcut = os.path.normpath(os.path.join(start_menu_dir, "NoiseClear.lnk"))

    if create_shortcut(start_shortcut, exe_path, icon_path, description, dist_dir):
        print(f"  Start Menu shortcut created: {start_shortcut}")
    else:
        print("  Failed to create Start Menu shortcut")

    print()
    print("=" * 50)
    print("NoiseClear deployed successfully!")
    print("=" * 50)
    print(f"  EXE:        {exe_path}")
    print(f"  Desktop:    {desktop_shortcut}")
    print(f"  Start Menu: {start_shortcut}")
    print()
    print("You can now launch NoiseClear from your Desktop")
    print("or by searching 'NoiseClear' in the Start Menu!")


if __name__ == "__main__":
    main()
