import neurokit2 as nk

# Load data
data, info = nk.read_xdf(
    "data/sub-P001/ses-S001/eeg/sub-P001_ses-S001_task-Default_run-001_eeg.xdf"
)

data = data.reset_index(drop=True)
data.plot(subplots=True)
