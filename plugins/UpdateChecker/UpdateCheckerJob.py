# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Message import Message
from UM.Version import Version
from UM.Logger import Logger
from UM.Job import Job

import urllib3
import platform
import json

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices


from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


##  This job checks if there is an update available on the provided URL.
class UpdateCheckerJob(Job):
    def __init__(self, silent = False, url = None):
        super().__init__()
        self.silent = silent
        self._url = url
        self._download_url = None  # If an update was found, the download_url will be set to the location of the new version.

    ##  Callback for the message that is spawned when there is a new version.
    def actionTriggered(self, message, action):
        if action == "download":
            if self._download_url is not None:
                QDesktopServices.openUrl(QUrl(self._download_url))

    def run(self):
        self._download_url = None  # Reset download ur.
        if not self._url:
            Logger.log("e", "Can not check for a new release. URL not set!")
        no_new_version = True

        application_name = Application.getInstance().getApplicationName()
        Logger.log("i", "Checking for new version of %s" % application_name)
        try:
            headers = {"User-Agent": "%s - %s" % (application_name, Application.getInstance().getVersion())}
            http = urllib3.PoolManager()
            latest_version_file = http.request("GET", self._url,headers=headers)
        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s" % e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information.")).show()
            return

        try:
            data = json.loads(latest_version_file.data.decode("utf-8"))
            try:
                if Application.getInstance().getVersion() is not "master":
                    local_version = Version(Application.getInstance().getVersion())
                else:
                    if not self.silent:
                        Message(i18n_catalog.i18nc("@info", "The version you are using does not support checking for updates.")).show()
                    return
            except ValueError:
                Logger.log("w", "Could not determine application version from string %s, not checking for updates", Application.getInstance().getVersion())
                if not self.silent:
                    Message(i18n_catalog.i18nc("@info", "The version you are using does not support checking for updates.")).show()
                return

            if application_name in data:
                for key, value in data[application_name].items():
                    if "major" in value and "minor" in value and "revision" in value and "url" in value:
                        os = key
                        if platform.system() == os: #TODO: add architecture check
                            newest_version = Version([int(value["major"]), int(value["minor"]), int(value["revision"])])
                            if local_version < newest_version:
                                Logger.log("i", "Found a new version of the software. Spawning message")
                                message = Message(i18n_catalog.i18nc("@info", "A new version is available!"))
                                message.addAction("download", i18n_catalog.i18nc("@action:button", "Download"), "[no_icon]", "[no_description]")
                                self._download_url = value["url"]
                                message.actionTriggered.connect(self.actionTriggered)
                                message.show()
                                no_new_version = False
                                break
                    else:
                        Logger.log("w", "Could not find version information or download url for update.")
            else:
                Logger.log("w", "Did not find any version information for %s." % application_name)
        except Exception:
            Logger.logException("e", "Exception in update checker while parsing the JSON file.")
            Message(i18n_catalog.i18nc("@info", "An exception occurred while checking for updates.")).show()
            no_new_version = False  # Just to suppress the message below.

        if no_new_version and not self.silent:
            Message(i18n_catalog.i18nc("@info", "No new version was found.")).show()