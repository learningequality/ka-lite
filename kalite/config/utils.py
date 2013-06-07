from kalite.utils.jobs import force_job
from config.models import Settings

def set_as_registered():
    force_job("syncmodels", "Secure Sync", "HOURLY")
    Settings.set("registered", True)

