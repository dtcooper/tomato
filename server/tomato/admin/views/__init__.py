from .asset_data import AdminAssetDataView
from .configure_live_clients import AdminConfigureLiveClientsView


extra_views = (AdminAssetDataView, AdminConfigureLiveClientsView)


__all__ = (extra_views,)
