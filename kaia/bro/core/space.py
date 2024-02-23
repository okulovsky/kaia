from .slot import Slot
from yo_fluq_ds import *
import pandas as pd
from ...infra.comm import IStorage



class ISpace:
    def get_name(self):
        return type(self).__name__


    def __post_init__(self):
        fields = vars(self)
        for k, v in fields.items():
            if isinstance(v, Slot):
                v._name = k


    def is_loggable(self):
        return True

    def get_slots(self) -> List[Slot]:
        fields = vars(self)
        result = []
        for k, v in fields.items():
            if isinstance(v, Slot):
                result.append(v)
        return result

    def get_slot(self, slot: str) -> Slot:
        value = getattr(self, slot)
        if not isinstance(value, Slot):
            raise ValueError(f'Field {slot} is not a Slot')
        return value

    def get_slots_as_dict(self) -> Dict[str, Slot]:
        return {s.name: s for s in self.get_slots()}

    def _history_iter(self, with_current, slots):
        all_slots = self.get_slots()
        if len(slots)==0:
            take_slots = all_slots
        else:
            take_slots = []
            for slot in slots:
                take = Query.en(all_slots).where(lambda z: z==slot).single_or_default()
                if take is None:
                    raise ValueError(f"Slot {slot} with name {slot.name} does not belong to the space {self}")
                take_slots.append(slot)

        if not with_current:
            iters = [iter(s.history) for s in take_slots]
        else:
            iters = [iter(s.history_with_current) for s in take_slots]

        while True:
            try:
                current = Obj()
                for slot, it in zip(take_slots, iters):
                    current[slot.name] = it.__next__()
                yield current
            except StopIteration:
                break


    def history(self, *slots):
        return Query.en(self._history_iter(False, slots))

    def history_with_current(self, *slots):
        return Query.en(self._history_iter(True, slots))

    def as_dict(self) -> Dict:
        result = dict()
        for slot in self.get_slots():
            result[slot.name] = slot.last_value
        return result

    def as_data_frame(self, amount: Optional[int] = None) -> pd.DataFrame:
        rows = []
        slots = self.get_slots()
        if amount is None:
            amount = len(slots[0]._history)
        for i in range(amount):
            row = {}
            stop = False
            for slot in slots:
                if len(slot._history)<=i:
                    stop = True
                    break
                row[slot.name] = slot._history[i]
            if stop:
                break
            rows.append(row)

        return pd.DataFrame(rows).sort_index(ascending=False).reset_index(drop=True)


    def get_current_values_as_dict(self) -> Dict:
        result = dict()
        for slot in self.get_slots():
            result[slot.name] = slot.current_value
        return result


    def restore_from_storage(self, storage: IStorage, count: Optional[int] = None):
        data = storage.load(self.get_name(), count, historical_order=False)
        slots = self.get_slots()
        history = {}
        for s in slots:
            history[s.name] = [c[s.name] if s.name in c else None for c in data]
        for s in slots:
            s._history = history[s.name]

    def setup_for_test(self, **slot_values: List):
        length = None
        for key, value in slot_values.items():
            if length is None:
                length = len(value)
            else:
                if len(value)!=length:
                    raise ValueError(f'All the arrays must have the same length. The length of the first key is {length}, the length of the key {key} was {len(value)}')
        placeholder = [None for _ in range(length - 1)]
        for slot in self.get_slots():
            if slot.name in slot_values:
                slot._history = slot_values[slot.name][:-1]
                slot._current_value = slot_values[slot.name][-1]
            else:
                slot._history = placeholder
                slot._current_value = None





TSpace = TypeVar('TSpace', bound=ISpace)
