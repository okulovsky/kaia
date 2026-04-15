import subprocess, os, signal

if __name__ == '__main__':
    result = subprocess.run(['fuser', '13002/tcp'], capture_output=True, text=True)
    pids = result.stdout.split()
    if not pids:
        print('No processes on port 13002')
    for pid in pids:
        os.kill(int(pid), signal.SIGKILL)
        print(f'Killed {pid}')
