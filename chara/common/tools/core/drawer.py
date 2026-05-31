from typing import Callable
from dataclasses import dataclass, field
from .interfaces import IDrawable, IDrawableCollection
import ipywidgets
from .selector import Selector
from copy import copy
from .orderer import Orderer
from .grouper import Grouper
from .table_view import TableView
from foundation_kaia.logging.html_log import HtmlLogItem


@dataclass
class Drawer:
    drawables: IDrawable|IDrawableCollection
    _groups: tuple[Selector,...] = ()
    _orderer: Orderer|None = None
    _table_view: TableView|None = None
    _metadata_to_print: tuple = ()

    def filter(self, filter: Callable[[IDrawable], bool]) -> 'Drawer':
        new_drawables = [self.drawables] if isinstance(self.drawables, IDrawable) else self.drawables.get_drawables()
        new_drawables = [d for d in new_drawables if filter(d)]
        drawer = copy(self)
        drawer.drawables = self.drawables.clone_for_other_set(new_drawables)
        return drawer


    def blocks(self,
               first_selector_or_column_count: str|Callable|int|None = None,
               second_selector: str|Callable|None = None,
               *metadata_to_print: str|Callable) -> 'Drawer':
        drawer = copy(self)
        if second_selector is not None:
            if isinstance(first_selector_or_column_count, int):
                raise ValueError("If second selector is set, first_selector cannot be int")
            drawer._orderer = Orderer(None, Selector(second_selector), Selector(first_selector_or_column_count))
        else:
            if isinstance(first_selector_or_column_count, int):
                drawer._orderer = Orderer(first_selector_or_column_count, None)
            elif first_selector_or_column_count is not None:
                drawer._orderer = Orderer(None, Selector(first_selector_or_column_count), None)
            else:
                drawer._orderer = Orderer(None, None, None)
        drawer._metadata_to_print = metadata_to_print
        return drawer

    def group(self, selector: str|Callable) -> 'Drawer':
        drawer = copy(self)
        drawer._groups += (Selector(selector),)
        return drawer



    def tables(self,
               head: int|None = None,
               order_by: str|Callable|None = None,
               ascending: bool = True,
               fields_to_exclude: list[str]|None = None,
               fields_to_include: list[str]|None = None) -> 'Drawer':
        drawer = copy(self)
        drawer._table_view = TableView(
            head,
            Selector(order_by) if order_by is not None else None,
            ascending,
            fields_to_exclude,
            fields_to_include
        )
        return drawer


    def _tile_html(self, d: IDrawable) -> str:
        lines = []
        for item in self._metadata_to_print:
            if callable(item):
                val = item(d)
            else:
                val = getattr(d.metadata, item, None)
            if val is not None:
                lines.append(str(val))
        meta_html = ''
        if lines:
            meta_html = '<div style="font-size:11px;color:#555;margin-top:4px">' + ''.join(
                f'<div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{line}">{line}</div>'
                for line in lines
            ) + '</div>'
        return d.to_html() + meta_html

    def _render_matrix(self, drawables: list[IDrawable], orderer: Orderer) -> str:
        col_keys = sorted(set(orderer.column_selector(d) for d in drawables))
        row_keys = sorted(set(orderer.row_selector(d) for d in drawables))
        lookup = {(orderer.row_selector(d), orderer.column_selector(d)): d for d in drawables}
        n_cols = len(col_keys)
        header = '<tr><th></th>' + ''.join(
            f'<th style="padding:4px;text-align:center;white-space:normal;word-break:break-all">{c}</th>' for c in col_keys
        ) + '</tr>'
        body_rows = []
        for rk in row_keys:
            body_rows.append(
                f'<tr><td colspan="{n_cols + 1}" style="padding:4px;background:#f0f0f0;font-weight:bold">{rk}</td></tr>'
            )
            cells = ['<td></td>']
            for ck in col_keys:
                d = lookup.get((rk, ck))
                if d is None:
                    cells.append('<td></td>')
                else:
                    cells.append(f'<td style="padding:4px">{self._tile_html(d)}</td>')
            body_rows.append('<tr>' + ''.join(cells) + '</tr>')
        return f'<table border="1" style="border-collapse:collapse">{header}{"".join(body_rows)}</table>'

    def html(self) -> HtmlLogItem:
        parts = []
        grouper = Grouper(list(self._groups))
        drawables = [self.drawables] if isinstance(self.drawables, IDrawable) else list(self.drawables.get_drawables())
        for section in grouper.group(drawables):
            if section.group_key is not None:
                parts.append(f'<h{section.group_level+1}>{section.group_key}</h{section.group_level+1}>')
            elif section.drawables is not None:
                if self._table_view is not None:
                    table = self._table_view.build_table(section.drawables)
                    header = '<tr><th></th>' + ''.join(f'<th>{c}</th>' for c in table.columns) + '</tr>'
                    body = ''.join(
                        '<tr><td>' + row.drawable.to_html() + '</td>'
                        + ''.join(f'<td>{v if v is not None else ""}</td>' for v in row.values)
                        + '</tr>'
                        for row in table.rows
                    )
                    parts.append(f'<table border="1" style="border-collapse:collapse">{header}{body}</table>')
                else:
                    orderer = self._orderer if self._orderer is not None else Orderer(None, None, None)
                    if orderer.column_selector is not None and orderer.row_selector is not None:
                        parts.append(self._render_matrix(section.drawables, orderer))
                    else:
                        n_cols = orderer.column_count
                        cols_css = f'repeat({n_cols},1fr)' if n_cols else 'repeat(auto-fill,minmax(200px,1fr))'
                        all_drawables = [d for r in orderer.build_table(section.drawables).rows for d in r if d is not None]
                        tiles = [
                            f'<div style="border:1px solid #ddd;border-radius:4px;padding:6px;min-width:0;overflow:hidden">'
                            f'{self._tile_html(d)}</div>'
                            for d in all_drawables
                        ]
                        parts.append(f'<div style="display:grid;grid-template-columns:{cols_css};gap:8px;margin-bottom:8px">{"".join(tiles)}</div>')
        return HtmlLogItem(''.join(parts))

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
