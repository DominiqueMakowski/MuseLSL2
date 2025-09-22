import neurokit2 as nk
import pyxdf



ppt = "P050"
path = f"data/sub-{ppt}/ses-S001/eeg/sub-{ppt}_ses-S001_task-Default_run-001_eeg.xdf"

# # Load data
data, info = nk.read_xdf(path)

data = data.reset_index(drop=True)
data.plot(subplots=True)

# data["Right AUX"]


streams, header = pyxdf.load_xdf(path)

pd.DataFrame(streams[0]["time_series"]).plot(subplots=True)
pd.DataFrame(streams[1]["time_series"]).plot(subplots=True)
pd.DataFrame(streams[2]["time_series"]).plot(subplots=True)
pd.DataFrame(streams[3]["time_series"]).plot(subplots=True)