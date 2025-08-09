import requests
from typing import Any, Dict, List, Optional
from foundation_kaia.marshalling import ApiUtils
from .message_format import MessageFormat
from ...messaging import IMessage

class MessagingAPI:
    def __init__(self, address: str):
        ApiUtils.check_address(address)
        self.address = address

    def add(self, session: str, message: IMessage, ) -> None:
        body = MessageFormat.to_json(message, session)
        r = requests.post(f"http://{self.address}/messages/add", json=body)
        r.raise_for_status()


    def get(self,
            session: Optional[str] = None,
            last_message_id: Optional[str] = None,
            count:   Optional[int] = None,
    ) -> List[IMessage]:
        params: Dict[str, Any] = {}
        if session is not None:
            params["session"] = session
        if last_message_id is not None:
            params["last_message_id"] = last_message_id
        if count is not None:
            params["count"] = count

        r = requests.get(f"http://{self.address}/messages/get", params=params)
        r.raise_for_status()
        return [MessageFormat.from_json(js) for js in r.json()]

    def last(
        self,
        session: Optional[str] = None,
    ) -> str|None:
        params: Dict[str, Any] = {}
        if session is not None:
            params["session"] = session

        r = requests.get(f"http://{self.address}/messages/last", params=params)
        r.raise_for_status()
        return r.json()['id']

