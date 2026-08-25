from dataclasses import dataclass

@dataclass
class SceneSettings:
    max_messages_in_continuation: int = 30
    max_sentences_in_summary: int = 3
    desired_user_messages_count_in_scene: int = 10
    intro: str|None = None
    message_length_in_words: int = 25
    min_messages_for_shortening: int = 15
    min_messages_after_shortening: int = 5
