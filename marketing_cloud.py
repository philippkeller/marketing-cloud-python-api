#!/usr/bin/env python

import requests
import json
import datetime
import uuid
import boto3

"""
To send emails over marketing cloud you need to do the following in the UI

1. create an 'email message' in Email > Content. This is the template 
    used for sending the mail
2. create a 'list' in Subscribers > List. This serves as a placeholder
    (has no actual use afaik)
3. create a 'data extension' in Subscribers > Data Extensions > 
    Create > Standard Data Extension > Create from Template > 
    TriggeredSendDataExtension
    It is important that you choose TriggeredSendDataExtension as
    the template

the usage then is the following:

>>> mc = MarketingCloud(client_id, secret_id, subdomain, account_id)
>>> definitionKey = 'my-identifier'

this is the customer key (an id with dashes) of the email message from step 1:
>>> customerKey = '…'

this is the external key of the list from step 2
>>> subscriptionList = '…'

this is the external key of the data extension from step 3
>>> dataExtension = '…'

the email definition puts the three steps into a relation
you can later reuse, so the create_email_definition needs to
be done only once per combination of the three steps.
>>> if not check_email_definition(dataExtension):
>>>     mc.create_email_definition(definitionKey, 'My Email Definition',
                                  'Description…', customerKey, dataExtension)

now you can start sending mails like this.
IMPORTANT: the key of the dict need to match exactly the dataExtension
(including upper/smaller case) otherwise the send_email succeeds but
the mail is never sent…
>>> mc.send_email(definitionKey, 'hans@meier.ch', dict(template_var1='Kurt'))

"""

class MarketingCloud():

  def __init__(self, client_id, secret_id, subdomain, account_id):
    """
    client_id, secret_id, subdomain, account_id: see in 
    Marketing Cloud > Setup > Apps > Installed Packages > Api
    subdomain: alphanumeric in the form of'abc01abcd0ab0abc01a01abc0ab0'
    account_id: numerical, e.g. 1234567
    """
    self.AUTH_BASE_URI = f'https://{subdomain}.auth.marketingcloudapis.com'
    self.REST_BASE_URI = f'https://{subdomain}.rest.marketingcloudapis.com'
    self.authorize(client_id, secret_id, account_id)

  def authorize(self, client_id, secret_id, account_id):
    # for documentation see https://developer.salesforce.com/docs/atlas.en-us.mc-app-development.meta/mc-app-development/integration-s2s-client-credentials.htm
    data = {"grant_type": "client_credentials",
    "clientId": client_id,
    "clientSecret": secret_id,
    "scope": "email_read email_write email_send",
    "account_id": account_id
    }

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    res = requests.post(f'{self.AUTH_BASE_URI}/v1/requestToken', 
                        data=json.dumps(data), headers=headers).json()
    access_token = res['accessToken']
    headers['Authorization'] = f'Bearer {access_token}'
    self._headers = headers
    self._access_token = access_token

  def check_email_definition(self, data_extension_key):
    """
    check if email definition with certain key already exists
    """
    url = f'{self.REST_BASE_URI}/messaging/v1/email/definitions/{data_extension_key}'
    res = requests.get(url, headers=self._headers)
    if res.status_code == 200:
      return True
    return False

  def send_email(self, definitionKey, email, data):
    """
    send the actual email, based on a created email definition

    arguments:
    - definitionKey, see create_email_definition
    - email: the to-email-address
    - data: the dict sent to the template, need to match EXACTLY the
            keys of the dataExtension (including upper/smaller)
            Values can include HTML

    return response of the api, e.g.:
    {"requestId":"a01234a1-05a1-4116-8503-ab0123a0a0a0","errorcode":0,"responses":[{"messageKey":"432a987f-ab01-012a-0123-0a01a0a0ab01"}]}

    raise Exception if email send fails
    """

    # for documentation see https://developer.salesforce.com/docs/atlas.en-us.mc-apis.meta/mc-apis/sendMessageSingleRecipient.htm
    data_out = dict(definitionKey=definitionKey, recipient=dict(
      contactKey=email,
      to=email,
      attributes=data))
    print(email, data_out)
    _id = str(uuid.uuid4())
    url = f'{self.REST_BASE_URI}/messaging/v1/email/messages/{_id}'
    res = requests.post(url, data=json.dumps(data_out), headers=self._headers)
    if res.status_code == 202:
      return res.json()
    raise Exception(res.text)


  def create_email_definition(self, definitionKey, name, description, customerKey, subscriptionList, dataExtension):
    """
    needs to be called prior to calling send_email()
    you can check if an email definition is already created with
    check_email_definition()

    arguments:
    - definitionKey:    arbitrary string, is used as a key in send_email()
    - name:             needs to be unique as well (wtf…) so you cannot create
                        separate send definitions with the same name.
                        There's a max length on the name, so keep this
                        one short and put the rest into description
    - description:      actually not sure where this is visible 
                        in the UI
    - customerKey:      key of the template to be taken for the mailing
    - subscriptionList: needs to exist in salesforce, create it in
                        email > subscribers > lists
    - dataExtension:    external key of data extension

    """

    # for documentation see https://developer.salesforce.com/docs/atlas.en-us.mc-apis.meta/mc-apis/createSendDefinition.htm
    data = {
      "definitionKey": definitionKey,
      "status": "Active",
      "name": name,
      "description": description,
      "classification": "Default Transactional",
      "content": {
        "customerKey": customerKey
      },
      "subscriptions": {
        "list": subscriptionList,
        "autoAddSubscriber": True,
        "updateSubscriber": True,
        "dataExtension": dataExtension
      },
      "options": {
        "trackLinks": True,
      }
    }
    res = requests.post(f'{self.REST_BASE_URI}/messaging/v1/email/definitions', 
                        data=json.dumps(data), headers=self._headers)
    if res.status_code != 201:
      raise Exception(res.text)

