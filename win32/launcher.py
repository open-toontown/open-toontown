#!/usr/bin/env python3
"""
Unified launcher for Open Toontown (TTBTN).

Starts the full local server stack (Astron -> UberDOG -> AI) and the game
client from a single console window, interleaving their logs with color
coding and offering a client relaunch loop.  No more juggling four windows.

Port of the "SUPER CFO UNIFIED LAUNCHER", adapted to this source's layout:
  * Server entry points (AIStart / UDStart) are configured via command-line
    arguments instead of environment variables (see win32/start_*.bat).
  * The bundled Python interpreter is read from the PPYTHON_PATH file.
  * Astron lives under astron/win32/ and must be launched from that folder
    so the relative paths in astrond.yml resolve correctly.
  * The client is started with toontown.launcher.QuickStartLauncher and the
    LOGIN_TOKEN environment variable (tt-specific-login).
"""

import ctypes
import json
import os
import socket
import subprocess
import sys
import threading
import time

# Enable ANSI escape processing on the Windows console
COLOR_SYSTEM = "\033[97;1m"    # Bold White
COLOR_ASTRON = "\033[96m"      # Cyan
COLOR_UBERDOG = "\033[92m"     # Green
COLOR_AI = "\033[93m"          # Yellow
COLOR_CLIENT = "\033[95m"      # Magenta
COLOR_RESET = "\033[0m"

# Fixed infrastructure ports (must match astron/config/astrond.yml)
EVENTLOGGER_IP = "127.0.0.1:7197"
STATESERVER = "4002"
CLIENT_AGENT_PORT = 7198

# Thread-safe printer
print_lock = threading.Lock()


def enable_ansi():
    if os.name == 'nt':
        try:
            kernel32 = ctypes.windll.kernel32
            h_stdout = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)
        except Exception:
            pass


def safe_print(prefix, color_code, text):
    with print_lock:
        encoding = sys.stdout.encoding or 'utf-8'
        for line in text.splitlines():
            cleaned = line.encode(encoding, errors='replace').decode(encoding)
            sys.stdout.write("%s%-10s | %s%s\n" % (color_code, prefix, cleaned, COLOR_RESET))
        sys.stdout.flush()


# Stream reader for subprocess output
def stream_reader(pipe, prefix, color_code):
    try:
        for line in iter(pipe.readline, b''):
            try:
                line_str = line.decode('utf-8', errors='replace')
            except Exception:
                line_str = line.decode('cp1252', errors='replace')
            safe_print(prefix, color_code, line_str.rstrip('\r\n'))
    except Exception as e:
        safe_print("[System]", COLOR_SYSTEM, "Error reading output from %s: %s" % (prefix, e))


def find_python(root):
    """Resolve the bundled interpreter via the PPYTHON_PATH file (sys.executable fallback)."""
    pp = None
    try:
        with open(os.path.join(root, 'PPYTHON_PATH'), 'r', encoding='utf-8') as f:
            pp = f.read().strip()
    except Exception:
        pass
    if pp:
        if not os.path.isabs(pp):
            pp = os.path.join(root, pp)
        pp = os.path.normpath(pp)
        if os.path.isfile(pp):
            return pp
        safe_print("[System]", COLOR_SYSTEM, "PPYTHON_PATH points to a missing file (%s); falling back to %s" % (pp, sys.executable))
        return sys.executable
    safe_print("[System]", COLOR_SYSTEM, "PPYTHON_PATH not found; falling back to %s" % sys.executable)
    return sys.executable


def find_astrond(root):
    candidates = [
        os.path.join(root, 'astron', 'win32', 'astrond.exe'),
        os.path.join(root, 'astron', 'astrond.exe'),
        os.path.join(root, 'astron', 'bin', 'astrond.exe'),
        os.path.join(root, 'astron', 'astrond'),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def split_host_port(value, default_port):
    host = value
    port = default_port
    if ':' in value:
        host, port = value.rsplit(':', 1)
        try:
            port = int(port)
        except ValueError:
            port = default_port
    return host, port


def is_tcp_open(host, port, timeout_s=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def wait_for_port(host, port, timeout_s, label):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_tcp_open(host, port):
            return True
        time.sleep(0.25)
    safe_print("[System]", COLOR_SYSTEM, "Timed out waiting for %s (%s:%s)." % (label, host, port))
    return False


def configure_launcher(config, config_path, force_prompt=False):
    if not force_prompt:
        safe_print("[System]", COLOR_SYSTEM, "--------------------------------------------------------")
        safe_print("[System]", COLOR_SYSTEM, "Current saved settings:")
        safe_print("[System]", COLOR_SYSTEM, "  Player Name:    %s" % config['player_name'])
        safe_print("[System]", COLOR_SYSTEM, "  District Name:  %s" % config['district_name'])
        safe_print("[System]", COLOR_SYSTEM, "  Astron (MD) IP: %s" % config['astron_ip'])
        safe_print("[System]", COLOR_SYSTEM, "--------------------------------------------------------")

        try:
            use_saved = input("Use these settings? [Y/n]: ").strip().lower()
        except KeyboardInterrupt:
            raise
        except Exception:
            use_saved = 'y'
        if use_saved not in ('n', 'no'):
            return config

    # Prompt for each value
    new_config = {}
    try:
        val = input("Enter player name [%s]: " % config['player_name']).strip()
        new_config['player_name'] = val if val else config['player_name']

        val = input("Enter district name [%s]: " % config['district_name']).strip()
        new_config['district_name'] = val if val else config['district_name']

        val = input("Enter Astron IP (MessageDirector) [%s]: " % config['astron_ip']).strip()
        new_config['astron_ip'] = val if val else config['astron_ip']
    except KeyboardInterrupt:
        raise
    except Exception as e:
        safe_print("[System]", COLOR_SYSTEM, "Error reading input: %s. Using defaults." % e)
        return config

    try:
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=4)
        safe_print("[System]", COLOR_SYSTEM, "Settings saved to config file.")
    except Exception as e:
        safe_print("[System]", COLOR_SYSTEM, "Could not save config file: %s" % e)

    return new_config


def main():
    enable_ansi()

    # Compute directories
    win32_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(win32_dir)

    # Load configuration
    config_path = os.path.join(win32_dir, "launcher_config.json")
    defaults = {
        "player_name": "dev",
        "district_name": "Toon Valley",
        "astron_ip": "127.0.0.1:7199"
    }
    config = defaults.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    config[k] = v
        except Exception as e:
            safe_print("[System]", COLOR_SYSTEM, "Error loading config file: %s" % e)
    check_dependencies = bool(config.get('check_dependencies', True))

    # Locate the bundled interpreter and astron binary
    ppython_path = find_python(root_dir)
    astrond = find_astrond(root_dir)
    if astrond is None:
        safe_print("[System]", COLOR_SYSTEM, "ERROR: Astron binary not found under astron/ (expected astron/win32/astrond.exe)!")
        sys.exit(1)
    astron_win32_dir = os.path.join(root_dir, 'astron', 'win32')

    # Prompt user
    safe_print("[System]", COLOR_SYSTEM, "========================================================")
    safe_print("[System]", COLOR_SYSTEM, "          OPEN TOONTOWN UNIFIED LAUNCHER               ")
    safe_print("[System]", COLOR_SYSTEM, "========================================================")

    try:
        config = configure_launcher(config, config_path, force_prompt=False)
    except KeyboardInterrupt:
        safe_print("[System]", COLOR_SYSTEM, "Aborted.")
        sys.exit(0)

    # Dependency verification (optional; set "check_dependencies": false in the
    # config to skip. Non-fatal and bounded so it can never hang the launcher.)
    req_file = os.path.join(root_dir, "requirements.txt")
    if check_dependencies and os.path.exists(req_file):
        safe_print("[System]", COLOR_SYSTEM, "Verifying dependency installation...")
        try:
            subprocess.run(
                [ppython_path, "-m", "pip", "install", "-q", "-r", req_file],
                timeout=90,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            safe_print("[System]", COLOR_SYSTEM, "Warning: Python dependency check returned error: %s" % e)

    # Build commands (this source configures servers via CLI args, see win32/start_*.bat)
    md_host, md_port = split_host_port(config['astron_ip'], 7199)

    astron_cmd = [astrond, "--loglevel", "info", "../config/astrond.yml"]

    ud_cmd = [
        ppython_path, "-u", "-m", "toontown.uberdog.UDStart",
        "--base-channel", "1000000",
        "--max-channels", "999999",
        "--stateserver", STATESERVER,
        "--messagedirector-ip", config['astron_ip'],
        "--eventlogger-ip", EVENTLOGGER_IP,
    ]

    ai_cmd = [
        ppython_path, "-u", "-m", "toontown.ai.AIStart",
        "--base-channel", "401000000",
        "--max-channels", "999999",
        "--stateserver", STATESERVER,
        "--messagedirector-ip", config['astron_ip'],
        "--eventlogger-ip", EVENTLOGGER_IP,
        "--district-name", config['district_name'],
    ]

    client_env = os.environ.copy()
    client_env["LOGIN_TOKEN"] = config['player_name']
    client_cmd = [ppython_path, "-u", "-m", "toontown.launcher.QuickStartLauncher"]

    active_processes = {}

    def cleanup():
        safe_print("[System]", COLOR_SYSTEM, "Shutting down all background processes...")
        # Terminate gently first (reverse startup order: AI, UberDOG, Astron)
        for name in ["AI", "Uberdog", "Astron"]:
            p = active_processes.get(name)
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        time.sleep(1.0)
        # Kill if still alive
        for name in ["AI", "Uberdog", "Astron"]:
            p = active_processes.get(name)
            if p and p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
        active_processes.clear()

    def servers_running():
        alive = True
        for name in ["Astron", "Uberdog", "AI"]:
            p = active_processes.get(name)
            if p and p.poll() is not None:
                safe_print("[System]", COLOR_SYSTEM, "WARNING: %s server is not running (exited early)." % name)
                alive = False
        return alive

    try:
        # Start Astron
        safe_print("[System]", COLOR_SYSTEM, "Starting Astron...")
        p = subprocess.Popen(astron_cmd, cwd=astron_win32_dir,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        active_processes["Astron"] = p
        threading.Thread(target=stream_reader, args=(p.stdout, "[Astron]", COLOR_ASTRON), daemon=True).start()

        if not wait_for_port(md_host, md_port, timeout_s=45, label="MessageDirector"):
            safe_print("[System]", COLOR_SYSTEM, "Astron may not be ready; continuing anyway...")

        # Start Uberdog
        safe_print("[System]", COLOR_SYSTEM, "Starting UberDOG...")
        p = subprocess.Popen(ud_cmd, cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        active_processes["Uberdog"] = p
        threading.Thread(target=stream_reader, args=(p.stdout, "[Uberdog]", COLOR_UBERDOG), daemon=True).start()
        time.sleep(1.0)

        # Start AI
        safe_print("[System]", COLOR_SYSTEM, "Starting AI (district '%s')..." % config['district_name'])
        p = subprocess.Popen(ai_cmd, cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        active_processes["AI"] = p
        threading.Thread(target=stream_reader, args=(p.stdout, "[AI]", COLOR_AI), daemon=True).start()

        # Give UberDOG/AI a moment to register with the cluster before the client
        # tries to log in (the client-agent port opens as soon as Astron is up).
        safe_print("[System]", COLOR_SYSTEM, "Waiting for UberDOG/AI to come online...")
        time.sleep(5.0)

        # Client loop (allows restarting without restarting the servers)
        while True:
            servers_running()

            # Wait for the client agent (7198) so the client never races a cold start
            if not is_tcp_open(md_host, CLIENT_AGENT_PORT, timeout_s=0.5):
                wait_for_port(md_host, CLIENT_AGENT_PORT, timeout_s=30, label="Client Agent")

            safe_print("[System]", COLOR_SYSTEM, "Starting game client for '%s'..." % client_env["LOGIN_TOKEN"])
            p_client = subprocess.Popen(client_cmd, cwd=root_dir, env=client_env,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            active_processes["Client"] = p_client
            threading.Thread(target=stream_reader, args=(p_client.stdout, "[Client]", COLOR_CLIENT), daemon=True).start()

            # Wait for client to exit
            while p_client.poll() is None:
                time.sleep(0.5)
                for name in ["Astron", "Uberdog", "AI"]:
                    proc = active_processes.get(name)
                    if proc and proc.poll() is not None and name in active_processes:
                        safe_print("[System]", COLOR_SYSTEM, "WARNING: %s process has stopped running!" % name)
                        del active_processes[name]

            safe_print("[System]", COLOR_SYSTEM, "Client process has exited.")
            active_processes.pop("Client", None)

            # Provide options to relaunch client or quit
            safe_print("[System]", COLOR_SYSTEM, "Options: [R]elaunch Client | [C]hange Settings & Relaunch | [Enter] to exit all")
            try:
                choice = input("Enter choice: ").strip().lower()
            except KeyboardInterrupt:
                break
            except Exception:
                choice = ''

            if choice == 'r':
                continue
            elif choice == 'c':
                # Force prompt for config (district name applies after a full restart)
                try:
                    config = configure_launcher(config, config_path, force_prompt=True)
                except KeyboardInterrupt:
                    break
                client_env["LOGIN_TOKEN"] = config['player_name']
                continue
            else:
                break

    except KeyboardInterrupt:
        safe_print("[System]", COLOR_SYSTEM, "Interrupted by user.")
    finally:
        cleanup()
        safe_print("[System]", COLOR_SYSTEM, "Unified launcher finished.")


if __name__ == "__main__":
    main()
