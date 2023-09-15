def view(
    window=5,
    scale=100,
    refresh=0.2,
    figure="15x6",
    version=1,
    backend="TkAgg",
    data_source="EEG",
    filter=True,
):
    from .viewer import viewer_v2

    viewer_v2.view()
