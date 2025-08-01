from dataclasses import dataclass
from datetime import datetime
from flask import send_from_directory, Response
from ..daemon import RecordingApi
from avatar.messaging import StreamClient
from avatar.services import SoundEvent


@dataclass
class FileRecord:
    filename: str       # e.g. "recording1.wav"
    timestamp: datetime # modification time of the file


class UploadedFileController:
    def __init__(self, client: StreamClient, recording_api: RecordingApi, limit: int = 50):
        self.recording_api = recording_api
        self.client = client
        self.records = []
        self.limit = limit



    def get_list_html(self) -> str:
        messages = self.client.pull()
        for message in messages:
            if isinstance(message, SoundEvent):
                self.records.append(FileRecord(message.file_id, message.envelop.timestamp))
        self.records = list(sorted(self.records, key = lambda z: z.timestamp, reverse = True))
        self.records = self.records[-self.limit:]

        html_parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'><title>Uploaded Audio Files</title>",
            "<style>",
            "  body { font-family: sans-serif; padding: 20px; }",
            "  table { border-collapse: collapse; width: 100%; }",
            "  th, td { padding: 8px; border-bottom: 1px solid #ddd; }",
            "  th { text-align: left; }",
            "  audio { width: 200px; }",
            "</style>",
            "</head><body>",
            "<h1>Recorded WAV Files</h1>",
            "<table>",
            "  <thead><tr><th>Timestamp</th><th>Filename</th><th>Play</th></tr></thead>",
            "  <tbody>"
        ]

        for rec in self.records:
            ts_str = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            html_parts.append(
                f"    <tr>"
                f"<td>{ts_str}</td>"
                f"<td>{rec.filename}</td>"
                f"<td><audio controls>"
                f"<source src=\"/play/{rec.filename}\" type=\"audio/wav\">"
                f"Your browser does not support the audio element."
                f"</audio></td>"
                f"</tr>"
            )

        html_parts.extend([
            "</tbody>",
            "</table>",
            "</body></html>"
        ])

        return "\n".join(html_parts)

    def serve_file(self, filename: str) -> Response:
        """
        Fetch the WAV bytes from the recording API and return
        an HTTP response with the correct audio MIME type.
        """
        try:
            wav_bytes = self.recording_api.download(filename)
        except Exception as e:
            # file not found or API error
            return Response(f"Error fetching '{filename}': {e}", status=404)

        return Response(
            wav_bytes,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"'
            }
        )
