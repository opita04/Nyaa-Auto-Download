"""
UI Panels for Nyaa Auto Download application.
Contains individual panel components for episodes, search, bulk operations, and settings.
"""

# Import actual panel classes
from .settings_panel import SettingsPanel
from .bulk_panel import BulkPanel

# TODO: Import other panels once they are implemented
# from .episodes_panel import EpisodesPanel
# from .search_panel import SearchPanel

# Placeholder classes for panels not yet implemented
class EpisodesPanel:
    """Placeholder for episodes panel."""
    pass

class SearchPanel:
    """Placeholder for search panel."""
    pass

__all__ = ['EpisodesPanel', 'SearchPanel', 'BulkPanel', 'SettingsPanel']
