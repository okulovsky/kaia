from pathlib import Path
from chara.common.cache import ICache, FileCache, MultifileCache
from chara.common.pipelines import logger
from chara.common import CharaApis
from brainbox.deciders import Chroma, Collector
from .dataset import IntentUtterance


class IntentRecognitionCache(ICache):
    def __init__(self, path: Path):
        super().__init__(path)
        self.train = FileCache()
        self.test_neighbors = MultifileCache()
        self.neg_neighbors = MultifileCache()


class IntentRecognitionPipeline:
    K_MAX = 9

    def __call__(
        self,
        cache: IntentRecognitionCache,
        train: list[IntentUtterance],
        test: list[IntentUtterance],
        negatives: list[str],
    ):
        @logger.phase(cache.train, "Training Chroma")
        def _():
            utterances = [{'text': u.text, 'intent': u.intent, 'language': u.language} for u in train]
            task_id = CharaApis.brainbox_api.add(Chroma.new_task().train(utterances))
            CharaApis.brainbox_api.join(task_id)
            cache.train.write(True)

        @logger.phase(cache.test_neighbors, "Getting test neighbors")
        def _():
            builder = Collector.TaskBuilder()
            for i, u in enumerate(test):
                builder.append(Chroma.new_task().find_neighbors(u.text, k=self.K_MAX), dict(index=i))
            results = CharaApis.brainbox_api.join(
                CharaApis.brainbox_api.add(builder.to_collector_pack('to_array'))
            )
            with cache.test_neighbors.session():
                for item in sorted(results, key=lambda x: x['tags']['index']):
                    cache.test_neighbors.write(item['result'])

        @logger.phase(cache.neg_neighbors, "Getting negatives neighbors")
        def _():
            with cache.neg_neighbors.session():
                if not negatives:
                    return
                builder = Collector.TaskBuilder()
                for i, text in enumerate(negatives):
                    builder.append(Chroma.new_task().find_neighbors(text, k=self.K_MAX), dict(index=i))
                results = CharaApis.brainbox_api.join(
                    CharaApis.brainbox_api.add(builder.to_collector_pack('to_array'))
                )
                for item in sorted(results, key=lambda x: x['tags']['index']):
                    cache.neg_neighbors.write(item['result'])

        cache.finalize()
