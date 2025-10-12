import subprocess


def run_espeak(data):
    text = data['text']
    text = '\n'.join(text)

    language = data.get('language', 'en-us')
    stress = data.get('stress', False)

    command = [
        '/home/app/.local/bin/espeak-phonemizer',
        '-v',
        language,
        '-p',
        '#',
        '-w',
        '$'
    ]

    if not stress:
        command.append('--no-stress')

    result = subprocess.check_output(
        command,
        input=text,
        text=True)

    result = [[s.split('#') for s in line.split('$')] for line in result.split('\n')[:-1]]
    return result