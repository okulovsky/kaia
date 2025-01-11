from dataclasses import dataclass

@dataclass
class OpenVoiceSettings:
    port: int = 11010                
    startup_time_in_seconds: int = 15
