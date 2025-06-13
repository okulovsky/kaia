from .scene import Scene, Medium, Character, CharacterPriority

def build_introduction(scene: Scene):
    prompt = []
    for character in scene.characters + (scene.user_character,):
        prompt.append(character.description)
    prompt.append(scene.context.intro)
    return '\n\n'.join(prompt)




def build_next_message_task(scene: Scene):
    prompt = [build_speakers_prompt(scene)]

    if scene.context.medium == Medium.default:
        if len(scene.characters) == 1:
            what = "Write a line for the dialog."
        else:
            what = "Write 1-2 lines for the dialog"
        what+=' '+SPEAK_FORMAT
    else:
        if len(scene.characters) == 1:
            what = 'Write a message for the messenger.'
        else:
            what = 'Write 1-2 messages for the messenger.'
        what+=' '+MESSENGER_FORMAT

    prompt.append(what)
    for character in scene.characters:
        prompt.append(character.style)
    prompt.append(f"Do not write anything for {scene.user_character.name}")
    prompt.append(f"Do not write more than 80 characters!")
    return "\n\n".join(prompt)


def build_current_scene(scene: Scene, add_progress: bool = True):
    prompt = []
    prompt.append(scene.context.scene_intro)
    prompt.extend(scene.context.intermediate_summaries)
    prompt.append("\n".join(str(m) for m in scene.messages))
    if add_progress and scene.progress.progress is not None:
        prompt.append(f"The scene is currently at {int(100*scene.progress.progress)}%.")
    return "\n\n".join(prompt)



def _name_list(characters: list[Character], mode='and'):
    if len(characters) == 0:
        raise ValueError("Empty characters list")
    if len(characters) == 1:
        return characters[0]
    return ', '.join(c.name for c in characters[:-1]) + ' ' + mode + ' ' + characters[-1].name


def build_speakers_prompt(scene: Scene):
    characters = scene.characters
    if len(characters) == 1:
        return f"Write a continuation of the scene by {characters[0].name}."
    level_to_character = {}
    for cis in characters:
        if cis.priority not in level_to_character:
            level_to_character[cis.priority] = []
        level_to_character[cis.priority].append(cis)
    if CharacterPriority.Leading not in level_to_character:
        if CharacterPriority.Supporting not in level_to_character:
            raise ValueError("Lead or Supporting characters must be present in the scene")
        else:
            level_to_character[CharacterPriority.Leading] = level_to_character[CharacterPriority.Supporting]
            del level_to_character[CharacterPriority.Supporting]
    all_speakers = level_to_character[CharacterPriority.Leading] + level_to_character.get(CharacterPriority.Supporting, [])
    prompt = [f'Write a continuation of the scene by {_name_list(all_speakers, "or")}.']
    if len(all_speakers) > 1:
        lead_speakers = level_to_character[CharacterPriority.Leading]
        lead = f'Most of the dialog should be driven by {_name_list(lead_speakers)}'
        if len(lead_speakers) > 1:
            lead += ', represented equally.'
        else:
            lead += '.'
        lead+='If someone is directly asked, they may answer without limitation.'
        prompt.append(lead)
        if CharacterPriority.Supporting in level_to_character:
            prompt.append(
                f'{_name_list(level_to_character[CharacterPriority.Supporting])} should also contribute, but less.')
    if CharacterPriority.Mentioned in level_to_character:
        prompt.append(
            f'{_name_list(level_to_character[CharacterPriority.Mentioned])} cannot speak directly, but can be mentioned by others.')

    return ' '.join(prompt)


FORMAT = '''
The line should not contain a newline symbol or quotes. Don't repeat what was already said in the dialog, ensure the action progresses, find new ideas and arguments, apply them appropriately depending on the other messages.
'''

SPEAK_FORMAT = '''
The line should contain the name of the speaker, then `:`, and then utterances and/or actions. Actions should be enclosed in `*` symbol. The example is: "John: Hey! *winks* Nice weather today, isn't it?".
'''

MESSENGER_FORMAT = '''
The line should start with the name of the speaker, then `:`, and then line should be a typical line in the messenger: text and maybe emojis. 
'''
