from .asset_data import AdminAssetDataView
from .configure_live_clients import AdminConfigureLiveClientsIFrameView, AdminConfigureLiveClientsView


extra_views = (AdminAssetDataView, AdminConfigureLiveClientsView, AdminConfigureLiveClientsIFrameView)


__all__ = (extra_views,)
