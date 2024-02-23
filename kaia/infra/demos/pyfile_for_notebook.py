
from IPython.display import HTML
from kaia.infra import FileIO
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

def py_to_notebook(files):
    html = []
    for file in files:
        html.append(f'<h3>{file.name}</h3>')
        text = FileIO.read_text(file)
        doc = []
        code = []
        in_doc = False
        for line in text.split('\n'):
            if line=='"""':
                in_doc = not in_doc
                continue
            if in_doc:
                doc.append(line)
            else:
                code.append(line)
        html.append(markdown.markdown('\n'.join(doc)))
        html.append('<br><br>')
        formatter = HtmlFormatter()
        python_code = highlight('\n'.join(code), PythonLexer(), formatter)
        html.append(f'<style>{formatter.get_style_defs()}</style>{python_code}')
    return HTML(''.join(html))