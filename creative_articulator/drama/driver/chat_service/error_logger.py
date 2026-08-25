import sys
from avatar.daemon import message_handler, ExceptionEvent


class ErrorLogger:
    @message_handler
    def on_error(self, event: ExceptionEvent) -> None:
        print(f"ERROR in {event.source}:\n{event.traceback}", file=sys.stderr, flush=True)
