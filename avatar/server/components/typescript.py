from pathlib import Path
import subprocess
import shutil
import re

import flask

from .avatar_component import IAvatarComponent

class TypeScriptComponent(IAvatarComponent):
    def __init__(self, ts_path: Path, compile_at_start_up: bool = False):
        self.ts_path = ts_path
        self.compile_at_start_up = compile_at_start_up


    def compile(self):
        TS_DIR = self.ts_path
        TSC_JS = TS_DIR / "node_modules" / "typescript" / "lib" / "tsc.js"
        shutil.rmtree(TS_DIR / 'dist', ignore_errors=True)
        NODE = subprocess.check_output(
            ['bash', '-ic', 'which node'],
            text=True
        ).strip()
        print("Using node at:", NODE)
        subprocess.run([
            NODE,
            str(TSC_JS),
            '-p', str(TS_DIR)
        ], cwd=str(TS_DIR), check=True)

        for js in (TS_DIR / 'dist').glob("*.js"):
            text = js.read_text()
            # this regex finds:  import … from './something';
            # and turns it into     import … from './something.js';
            new = re.sub(
                r"(import\s+[^;]+from\s+['\"])(\./[^'\"\.]+)(['\"])",
                r"\1\2.js\3",
                text
            )
            js.write_text(new)

    def get_typescript_file(self, path):
        return flask.send_from_directory(self.ts_path/'dist', path)


    def setup_server(self, app: IAvatarComponent.App, address: str):
        if self.compile_at_start_up:
            self.compile()
        app.add_url_rule(f'/scripts/<path:path>', view_func=self.get_typescript_file, methods=['GET'])

