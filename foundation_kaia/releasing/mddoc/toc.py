def create_toc(content: str):
    toc = []
    for line in content.split('\n'):
        if not line.startswith('#'):
            continue
        cnt = 0
        while line.startswith('#' * cnt):
            cnt += 1
        title = line[cnt:].strip()
        link = title.lower().replace(' ', '-')
        toc.append('  ' * (cnt - 2) + f'* [{title}](#{link})')
    return "\n".join(toc)