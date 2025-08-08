import requests
from typing import Any, Dict, List, Optional
from foundation_kaia.marshalling import ApiUtils, TestApi, Api
import uuid
from foundation_kaia.marshalling import ApiUtils

class MessagingAPI:
    def __init__(self, address: str):
        ApiUtils.check_address(address)
        self.address = address

    def add(
        self,
        message_type: str,
        session: Optional[str],
        envelop: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """
        POST /add
        Returns the created MessageRecord as a dict.
        Raises HTTPError on 4xx/5xx.
        """
        body = {
            "message_type": message_type,
            "envelop": envelop,
            "payload": payload,
            "session": session
        }

        r = requests.post(f"http://{self.address}/messages/add", json=body)
        r.raise_for_status()


    def get(
        self,
        session: Optional[str] = None,
        last_message_id: Optional[str] = None,
        count:   Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        GET /get
        Query‑params:
          session, last_message_id, count
        Returns a list of MessageRecord dicts.
        Raises HTTPError on 4xx/5xx.
        """
        params: Dict[str, Any] = {}
        if session is not None:
            params["session"] = session
        if last_message_id is not None:
            params["last_message_id"] = last_message_id
        if count is not None:
            params["count"] = count

        r = requests.get(f"http://{self.address}/messages/get", params=params)
        r.raise_for_status()
        return r.json()

    def last(
        self,
        session: Optional[str] = None,
    ) -> str|None:
        """
        GET /get
        Query‑params:
          session, last_message_id, count
        Returns a list of MessageRecord dicts.
        Raises HTTPError on 4xx/5xx.
        """
        params: Dict[str, Any] = {}
        if session is not None:
            params["session"] = session

        r = requests.get(f"http://{self.address}/messages/last", params=params)
        r.raise_for_status()
        return r.json()['id']

