from typing import Callable
from dataclasses import dataclass
from .interfaces import IDrawable, IDrawableCollection
import ipywidgets
from .selector import Selector
from copy import copy
from .orderer import Orderer
from .grouper import Grouper
from .table_view import TableView



@dataclass
class Drawer:
    drawables: IDrawable|IDrawableCollection
    _groups: tuple[Selector,...] = ()
    _orderer: Orderer|None = None
    _table_view: TableView|None = None

    def ordered_blocks(self, first_selector: str|Callable, second_selector: str|Callable|None = None) -> 'Drawer':
        drawer = copy(self)
        if second_selector is not None:
            drawer._orderer = Orderer(None, Selector(second_selector), Selector(first_selector))
        else:
            drawer._orderer = Orderer(None, Selector(first_selector), None)
        return drawer

    def blocks(self, column_count) -> 'Drawer':
        drawer = copy(self)
        self._orderer = Orderer(column_count)
        return drawer

    def group(self, selector: str|Callable) -> 'Drawer':
        drawer = copy(self)
        drawer._groups += (Selector(selector),)
        return drawer



    def tables(self,
               head: int|None = None,
               order_by: str|Callable|None = None,
               ascending: bool = True,
               exclude: list[str]|None = None,
               include: list[str]|None = None) -> 'Drawer':
        drawer = copy(self)
        drawer._table_view = TableView(
            head,
            Selector(order_by) if order_by is not None else None,
            ascending,
            exclude,
            include
        )
        return drawer


    def widget(self) -> ipywidgets.Widget:
        rows = []
        grouper = Grouper(list(self._groups))
        drawables = [self.drawables] if isinstance(self.drawables, IDrawable) else self.drawables.get_drawables()
        for section in grouper.group(drawables):
            if section.group_key is not None:
                rows.append(ipywidgets.HTML(f"<h{section.group_level+1}>{section.group_key}</h{section.group_level+1}>"))
            elif section.drawables is not None:
                if self._table_view is not None:
                    table = self._table_view.build_table(section.drawables)
                    rows.append(table.to_widget())
                else:
                    if self._orderer is not None:
                        orderer = self._orderer
                    else:
                        orderer = Orderer(None, None, None)
                    table = orderer.build_table(section.drawables)
                    for r in table.rows:
                        row_widgets = [d.to_widget() for d in r]
                        rows.append(ipywidgets.HBox(row_widgets))
        return ipywidgets.VBox(rows)






