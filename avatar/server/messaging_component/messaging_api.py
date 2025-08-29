import requests
from typing import Any, Dict, List, Optional
from foundation_kaia.marshalling import ApiUtils
from .message_format import MessageFormat, get_full_name_by_type
from ...messaging import IMessage

class MessagingAPI:
    def __init__(self, address: str):
        ApiUtils.check_address(address)
        self.address = address

    def add(self, session: str, message: IMessage, ) -> None:
        body = MessageFormat.to_json(message, session)
        r = requests.post(f"http://{self.address}/messages/add", json=body)
        if r.status_code!=200:
            raise ValueError(f"Server returned status {r.status_code}\n{r.text}")


    def get(self,
            session: Optional[str] = None,
            last_message_id: Optional[str] = None,
            count:   Optional[int] = None,
            types: tuple[type, ...] | None = None,
            except_types: tuple[type,...] | None = None
    ) -> List[IMessage]:
        params = dict(session = session, count = count, last_message_id = last_message_id)
        if types is not None:
            params['types'] = [get_full_name_by_type(t) for t in types]
        else:
            params['types'] = None
        if except_types is not None:
            params['except_types'] = [get_full_name_by_type(t) for t in except_types]
        else:
            params['except_types'] = None
        r = requests.post(f"http://{self.address}/messages/get", json=params)
        if r.status_code!=200:
            raise ValueError(f"Server returned status {r.status_code}\n{r.text}")
        return [MessageFormat.from_json(js) for js in r.json()]

    def tail(self,
             count: int,
             session: Optional[str] = None,
             types: tuple[type, ...] | None = None,
             except_types: tuple[type, ...] | None = None
             ):
        params = dict(session = session, count = count)
        if types is not None:
            params['types'] = [get_full_name_by_type(t) for t in types]
        else:
            params['types'] = None
        if except_types is not None:
            params['except_types'] = [get_full_name_by_type(t) for t in except_types]
        else:
            params['except_types'] = None
        r = requests.post(f"http://{self.address}/messages/tail", json=params)
        if r.status_code!=200:
            raise ValueError(f"Server returned status {r.status_code}\n{r.text}")
        return [MessageFormat.from_json(js) for js in r.json()]


    def last(
        self,
        session: Optional[str] = None,
    ) -> str|None:
        r = requests.post(f"http://{self.address}/messages/last", json=dict(session=session))
        if r.status_code!=200:
            raise ValueError(f"Server returned status {r.status_code}\n{r.text}")
        return r.json()['id']

