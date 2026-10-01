import subprocess

def set_volume(volume: float) -> None:
    value = max(0.0, min(0.7, volume))
    subprocess.run(
        ['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f'{value:.2f}'],
        capture_output=True, text=True, check=True
    )
