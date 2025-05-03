from brainbox.flow import Accessor, JsonCacheManager
from kaia.common import Loc
import requests

class Wiktionary(Accessor[str,str]):
    def __init__(self, language):
        self.language = language
        super().__init__(JsonCacheManager(Loc.temp_folder/'wiktionary'))

    def _translate_external_key(self, key: str) -> str:
        return self._hash_str(self.language+'/'+key)

    def _external_get(self, key: str):
        reply = requests.get(f'https://{self.language}.wiktionary.org/w/api.php?action=query&format=json&prop=revisions&titles={key}&rvprop=content')
        return dict(word=key, language=self.language, data=reply.json())

    def _postprocess(self, value):
        try:
            if 'query' not in value['data'] or 'pages' not in value['data']['query']:
                return None
            pages = value['data']['query']['pages']
            page = pages[list(pages)[0]]
            if 'revisions' not in page:
                return None
            revisions = page['revisions']
            if len(revisions) > 1:
                raise ValueError("No revisions")
            if len(revisions) == 0:
                return None
            return revisions[0]['*']
        except:
            print(value)
            raise