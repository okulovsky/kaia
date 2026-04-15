import subprocess

def set_volume(volume: float) -> None:
    percent = int(round(max(0.0, min(1.0, volume)) * 100))
    subprocess.run(
        ['amixer', 'sset', 'Master', f'{percent}%'],
        capture_output=True, text=True, check=True
    )

