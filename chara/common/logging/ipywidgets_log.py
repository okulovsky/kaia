import ipywidgets
import json
from ipywidgets.embed import embed_data
from dataclasses import dataclass
from .log_item import ILogItem

def widget_to_fragment(widget) -> str:
    """
    Produce a self-contained HTML fragment that embeds an ipywidget
    without <!DOCTYPE> or <html> wrappers.
    Suitable for inclusion inside any existing HTML page.
    """
    data = embed_data(views=[widget])

    manager_state_json = json.dumps(data["manager_state"])
    view_json = json.dumps(data["view_specs"][0])  # одна вьюха

    fragment = f"""
<!-- ipywidget fragment -->
<!-- RequireJS (нужен html-manager'у) -->
<script
  src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js"
  crossorigin="anonymous">
</script>

<!-- HTML widget manager -->
<script
  data-jupyter-widgets-cdn="https://unpkg.com/"
  data-jupyter-widgets-cdn-only
  src="https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@*/dist/embed-amd.js"
  crossorigin="anonymous">
</script>

<!-- Состояние всех моделей -->
<script type="application/vnd.jupyter.widget-state+json">
{manager_state_json}
</script>

<!-- Конкретный виджет -->
<script type="application/vnd.jupyter.widget-view+json">
{view_json}
</script>
""".strip()

    return fragment

@dataclass
class WidgetLogItem(ILogItem):
    widget: ipywidgets.Widget

    def to_html(self) -> str:
        return widget_to_fragment(self.widget)

    def to_string(self) -> str:
        return '[ipywidget]'