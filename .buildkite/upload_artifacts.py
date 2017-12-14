"""
# Requirements:
    * Generate access token in your Github account, then create environment variable GITHUB_ACCESS_TOKEN.
        - e.g export GITHUB_ACCESS_TOKEN=1ns3rt-my-t0k3n-h3re.
    * Generate a service account key for your Google API credentials, then create environment variable GOOGLE_APPLICATION_CREDENTIALS.
        - e.g export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json.
# Environment Variable/s:
    * IS_KALITE_RELEASE = Upload artifacts to the Google Cloud as a release candidate.
    * GITHUB_ACCESS_TOKEN = Personal access token used to authenticate in your Github account via API.
    * BUILDKITE_BUILD_NUMBER = Build identifier for each directory created.
    * BUILDKITE_PULL_REQUEST = Pull request issue or the value is false.
    * BUILDKITE_TAG = Tag identifier if this build was built from a tag.
    * BUILDKITE_COMMIT = Git commit hash that the build was made from.
    * GOOGLE_APPLICATION_CREDENTIALS = Your service account key.
"""

import logging
import os
import sys

import requests
from gcloud import storage
from github3 import login

logging.getLogger().setLevel(logging.INFO)

ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
REPO_OWNER = "learningequality"
REPO_NAME = "ka-lite"
ISSUE_ID = os.getenv("BUILDKITE_PULL_REQUEST")
BUILD_ID = os.getenv("BUILDKITE_BUILD_NUMBER")
TAG = os.getenv("BUILDKITE_TAG")
COMMIT = os.getenv("BUILDKITE_COMMIT")

RELEASE_DIR = 'release'
PROJECT_PATH = os.path.join(os.getcwd())

# Python packages artifact location
DIST_DIR = os.path.join(PROJECT_PATH, "dist")
# Installer artifact location
INSTALLER_DIR = os.path.join(PROJECT_PATH, "installer")

headers = {'Authorization': 'token %s' % ACCESS_TOKEN}

INSTALLER_CAT = "Installers"
PYTHON_PKG_CAT = "Python Packages"

# Manifest of files keyed by extension

file_manifest = {
    'exe': {
        'extension': 'exe',
        'description': 'Windows Installer',
        'category': INSTALLER_CAT,
        'content_type': 'application/x-ms-dos-executable',
    },
    'pex': {
        'extension': 'pex',
        'description': 'Pex file',
        'category': PYTHON_PKG_CAT,
        'content_type': 'application/octet-stream',
    },
    'whl': {
        'extension': 'whl',
        'description': 'Whl file',
        'category': PYTHON_PKG_CAT,
        'content_type': 'application/zip',
    },
    'gz': {
        'extension': 'gz',
        'description': 'Tar file',
        'category': PYTHON_PKG_CAT,
        'content_type': 'application/gzip',
    },
}

file_order = [
    'exe',
    'pex',
    'whl',
    'gz',
]

gh = login(token=ACCESS_TOKEN)
repository = gh.repository(REPO_OWNER, REPO_NAME)

def create_status_report_html(artifacts):
    """
    Create html page to list build artifacts for linking from github status.
    """
    html = "<html>\n<title>KA-Lite Buildkite Assets &ndash; Build #{build_id}</title>\n".format(build_id=BUILD_ID)
    html += "<body>\n<h1>Build Artifacts</h1>\n"
    current_heading = None

    for ext in file_order:
        artifacts_list = []

        for artifact_dict in artifacts:
            if artifact_dict['extension'] == ext:
                artifacts_list.append(artifact_dict)
        
        for artifact in artifacts_list: 
            if artifact['category'] != current_heading:
                current_heading = artifact['category']
                html += "<h2>{heading}</h2>\n".format(heading=current_heading)
            html += "<p>{description}: <a href='{media_url}'>{name}</a></p>\n".format(
            **artifact)
    html += "</body>\n</html>"
    return html

def create_github_status(report_url):
    """
    Create a github status with a link to the report URL,
    only do this once buildkite has been successful, so only report success here.
    """
    status = repository.create_status(
        COMMIT,
        "success",
        target_url=report_url,
        description="KA-Lite Buildkite assets",
        context="buildkite/kalite/assets"
    )

    if status:
        logging.info("Successfully created GitHub status for commit {commit}.".format(commit=COMMIT))
    else:
        logging.info("Error encountered. Now exiting!")
        sys.exit(1)

def collect_local_artifacts():
    """
    Create a list of artifacts
    """
    
    collected_artifacts = []

    def create_artifact_data(artifact_dir):
        for artifact in os.listdir(artifact_dir):
            filename, file_extension = os.path.splitext(artifact)
            file_extension = file_extension[1:] # Remove leading '.'

            if file_extension in file_manifest:
                data = {
                    'name': artifact,
                    'file_location': "{artifact_dir}/{artifact}".format(artifact_dir=artifact_dir, artifact=artifact)
                }
                data.update(file_manifest[file_extension])
                logging.info("Collecting file data: {data}".format(data=data))
                collected_artifacts.append(data)

    create_artifact_data(DIST_DIR)
    create_artifact_data(INSTALLER_DIR)

    return collected_artifacts

def upload_artifacts():
    """
    Upload the artifacts to the Google Cloud Storage
    Create a github status on the pull requester with the artifact media link.
    """

    client = storage.Client()
    bucket = client.bucket("le-downloads")
    artifacts = collect_local_artifacts()
    is_release = os.getenv("IS_KALITE_RELEASE")

    for artifact in artifacts:
        logging.info("Uploading file {filename}".format(filename=artifact.get("name")))

        if is_release:
            blob = bucket.blob("kalite-{release_dir}-{build_id}-{filename}".format(
                release_dir=RELEASE_DIR,
                build_id=BUILD_ID,
                filename=artifact.get("name")
            ))
        else:
            blob = bucket.blob("kalite-buildkite-build_{release_dir}-{build_id}-{filename}".format(
                release_dir=RELEASE_DIR, 
                build_id=BUILD_ID, 
                filename=artifact.get("name")
            ))
        
        blob.upload_from_filename(filename=artifact.get("file_location"))
        blob.make_public()
        artifact.update({'media_url': blob.media_link})

    html = create_status_report_html(artifacts)
    blob = bucket.blob("kalite-{release_dir}-{build_id}".format(release_dir=RELEASE_DIR, build_id=BUILD_ID))
    blob.upload_from_string(html, content_type='text/html')
    blob.make_public()

    logging.info("Status Report link: {}".format(blob.public_url))
    create_github_status(blob.public_url)

    if TAG:
        # Building from a tag, this is probably a release!
        get_release_asset_url = requests.get("https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}".format(
            owner=REPO_OWNER,
            repo=REPO_NAME,
            tag=TAG
        ))

        if get_release_asset_url.status_code == 200:
            release_id = get_release_asset_url.json()['id']
            release_name = get_release_asset_url.json()['name']
            release = repository.release(id=release_id)
            logging.info("Uploading build assets to GitHub Release: {release_name}".format(release_name=release_name))
            
            for ext in file_order:
                artifact_list = []
                for artifact_dict in artifacts:
                    if artifact_dict['extension'] == ext:
                        artifact_list.append(artifact_dict)
                
                for artifact in artifact_list:
                    logging.info("Uploading release asset: {artifact_name}".format(artifact.get('name')))
                    # For some reason github3 does not let us set a label at initial upload
                    asset = release.upload_asset(
                        content_type=['content_type'],
                        name=artifact['name'],
                        asset=open(artifact['file_location'], 'rb')
                    )

                    if asset:
                        # So do it after the initial upload instead
                        asset.edit(artifact['name'], label=artifact['description'])
                        logging.info("Successfully uploaded release asset: {artifact}".format(artifact=artifact.get('name')))
                    else:
                        logging.info("Error uploading release asset: {artifact}".format(artifact=artifact.get('name')))

def main():
    upload_artifacts()

if __name__ == "__main__":
    main()
