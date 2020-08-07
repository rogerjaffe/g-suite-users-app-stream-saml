from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']

# Reference this documentation for the instructions to add SAML authentication on G-Suite
# to access AppStream: https://aws.amazon.com/blogs/desktop-and-application-streaming/setting-up-g-suite-saml-2-0-federation-with-amazon-appstream-2-0/
# ROLE is the ARN created in Step 2, comma, ARN created in Step 3 of the documentation
# The ROLE is saved as a User Information Custom Attribute in G-Suite with the key
# SAML-USER-ATTRIBUTES
#
# This script adds the SAML user attributes to all users in the G-Suite domain.  See
# https://developers.google.com/admin-sdk/directory/v1/quickstart/python to enable G-Suite
# Admin API and download the credentials.json file in Step 1
#
IAM_ARN = 'arn:aws:iam::851803623504:role/AppStream'
IdP_ARN = 'arn:aws:iam::851803623504:saml-provider/Google'
ROLE = IAM_ARN+','+IdP_ARN
SESSION_DURATION = "3600"
ORG_UNIT_PATH = '/2020-2021'
DOMAIN = 'patrickhenryhs.net'

def get_credentials():
  """Shows basic usage of the Admin SDK Directory API.
  Prints the emails and names of the first 10 users in the domain.
  """
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
      creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
      pickle.dump(creds, token)

  return creds


def update_saml_attributes(service, user):
  custom_schema = {
    "SessionDuration": SESSION_DURATION,
    "FederationRole": ROLE
  }

  user.update({'customSchemas': {'SAML-USER-ATTRIBUTES': custom_schema}})
  ret = service.users().update(userKey=user['id'], body=user).execute()

  return ret['customSchemas']


def main():
  creds = get_credentials()
  pageToken = None

  service = build('admin', 'directory_v1', credentials=creds)

  # Call the Admin SDK Directory API
  # print('Getting the first 10 users in the domain')
  # The use of single quotes on the orgPath parameter allows OU paths with spaces
  orgPath = "orgUnitPath='"+ORG_UNIT_PATH+"'"

  while True:
    results = service.users().list(domain=DOMAIN,
                                   query=orgPath,
                                   # comment out maxResults to make changes to more than the first 10 users. This is currently set to limit errors affecting more than 10 users until you've tested the script
                                   # maxResults=10,
                                   pageToken=pageToken,
                                   orderBy='email').execute()
    pageToken = results.get('nextPageToken')
    if not pageToken:
      break;
    users = results.get('users', [])

    if not users:
      print('No users in the domain.')
    else:
      print('Updated users with the following customSchemas')
      for user in users:
        # Uncomment the following line to print users for confirmation/testing
        # print(u'{0} ({1})'.format(user['primaryEmail'], user['name']['fullName']))

        # The following will update the user customSchemas - comment out if you're only testing
        userUpdated = update_saml_attributes(service, user)
        print(u'{0} {1} {2} {3}'.format(user['primaryEmail'], user['name']['fullName'], user['id'], userUpdated))

    if not pageToken:
      break;


if __name__ == '__main__':
  main()