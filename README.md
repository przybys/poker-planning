# poker-planning

Poker Planning using [Google App Engine Python Standard Environment](https://cloud.google.com/appengine/docs/standard/python/).  
<http://poker-planning.appspot.com/>

## Setup

Make sure you have the [Google Cloud SDK](https://cloud.google.com/sdk/) installed.
You'll need this to test and deploy this application.

### Authentication

For running this application locally, you'll need to download a service account to
provide credentials that would normally be provided automatically in the App
Engine environment. Click the gear icon in the Firebase Console and select
'Permissions'; then go to the 'Service accounts' tab. Download a new or
existing App Engine service account credentials file. Then set the environment
variable `GOOGLE_APPLICATION_CREDENTIALS` to the path to this file:

    export GOOGLE_APPLICATION_CREDENTIALS=~/.google_application_credentials/poker-planning.json

### Install dependencies

Before running or deploying this application, install the dependencies using [pip](http://pip.readthedocs.io/en/stable/):

    pip install -t lib -r requirements.txt

## Running this application

    dev_appserver.py app.yaml
