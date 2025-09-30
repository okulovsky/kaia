from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List
from flask import abort, jsonify, request, send_file, Blueprint
from ..common import BlueprintComponent

class FileCacheComponent(BlueprintComponent):
    def __init__(self, base_dir: str | Path, url_prefix: str = "/file-cache"):
        self.base_dir = Path(base_dir)
        self.url_prefix = url_prefix


    def create_blueprint(self):
        name = f"file_cache_"+self.url_prefix.strip("/").replace("/", "_")

        bp = Blueprint(
            name,
            __name__,
            url_prefix=self.url_prefix
        )

        bp.add_url_rule(
            "/file/<path:filepath>",
            view_func=self.file_resource,
            methods=["GET", "PUT", "DELETE", "HEAD"]
        )

        bp.add_url_rule(
            "/dir/<path:dirpath>",
            view_func=self.dir_resource,
            methods=["GET", "HEAD"]
        )

        bp.add_url_rule("/", view_func=self.status, methods=['GET'])
        return bp


    def _secure_path(self, rel_path: str) -> Path:
        target = (self.base_dir / rel_path).resolve()
        if not str(target).startswith(str(self.base_dir) + os.sep) and target != self.base_dir:
            abort(400, description="Invalid path.")
        return target

    @staticmethod
    def _iter_chunks(stream, chunk_size: int = 1024 * 1024) -> Iterable[bytes]:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk


    def status(self):
        return jsonify(dict(status='ok'))

    def file_resource(self, filepath: str):
        path = self._secure_path(filepath)

        if request.method == "HEAD":
            if not path.is_file():
                abort(404)
            resp = jsonify()
            resp.headers["Content-Length"] = path.stat().st_size
            resp.status_code = 200
            return resp

        if request.method == "GET":
            if not path.is_file():
                abort(404, description="File not found.")
            return send_file(path, as_attachment=False, conditional=True)

        if request.method == "PUT":
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".part")
            with open(tmp_path, "wb") as f:
                for chunk in self._iter_chunks(request.stream):
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
            os.replace(tmp_path, path)
            return jsonify({"status": "ok", "path": str(path.relative_to(self.base_dir))})

        if request.method=='DELETE':
            if not path.is_file():
                abort(404, description="File not found.")
            path.unlink()
            return jsonify({"status": "ok"})

        raise ValueError(f"Unexpected method {request.method}")

    def dir_resource(self, dirpath: str):
        path = self._secure_path(dirpath)

        if request.method == "HEAD":
            if not path.is_dir():
                abort(404)
            return ("", 200)

        if request.method == "GET":
            if not path.is_dir():
                abort(404, description="Directory not found.")

            name_prefix = request.args.get("prefix")
            name_suffix = request.args.get("suffix")
            recursive = request.args.get("recursive", "0") in {"1", "true", "True", "yes"}

            results: List[str] = []
            if recursive:
                for root, _, files in os.walk(path):
                    for fn in files:
                        if name_prefix and not fn.startswith(name_prefix):
                            continue
                        if name_suffix and not fn.endswith(name_suffix):
                            continue
                        abs_path = Path(root) / fn
                        rel_to_dir = abs_path.relative_to(path)
                        results.append(str(rel_to_dir))
            else:
                for p in path.iterdir():
                    if p.is_file():
                        fn = p.name
                        if name_prefix and not fn.startswith(name_prefix):
                            continue
                        if name_suffix and not fn.endswith(name_suffix):
                            continue
                        results.append(fn)

            return jsonify(sorted(results))

