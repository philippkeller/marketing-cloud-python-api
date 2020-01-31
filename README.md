Small wrapper including documentation how to use the marketing cloud REST api.

The [official documentation](https://developer.salesforce.com/docs/atlas.en-us.noversion.mc-apis.meta/mc-apis/transactional-messaging-get-started.htm) is lacking at some spots, so this repo is meant as a starting point for building your own wrapper.

# How to send an email over marketing cloud

To send emails over marketing cloud you need to do the following in the UI (sadly the REST api does not cover these steps, the SOAP api is more complete but I couldn't motivate myself to step into the soap land…)

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

```python
from marketing_cloud import MarketingCloud
import datetime

mc = MarketingCloud(client_id, secret_id, subdomain, account_id)

# definitionKey is your choice. The docs recommend a new key every week.
# also, if you change the email template you need a new email definition
# (-> new definitionKey), otherwise the change is not taken
suffix = datetime.date.today().strftime('%W')
definitionKey = f'my-identifier-week-{suffix}'

# the email definition puts the three steps into a relation
# you can later reuse, so the create_email_definition needs to
# be done only once per combination of the three steps.
if not check_email_definition(definitionKey):
    # this is the customer key (an id with dashes) of the email message from step 1:
    customerKey = '…'

    # this is the external key of the list from step 2
    subscriptionList = '…'

    # this is the external key of the data extension from step 3
    dataExtension = '…'

    # name needs to be unique
    name = f"My Mailing {suffix}" 
    mc.create_email_definition(definitionKey, name,
                              'Description…', customerKey, dataExtension)

```

Now you can start sending mails.  *Important*: the key of the dict need to match exactly the dataExtension
(including upper/smaller case) otherwise the send_email succeeds but
the mail is never sent…:

```python
mc.send_email(definitionKey, 'hans@meier.ch', dict(template_var1='Kurt'))
```

## Reports

As this is not a promotional mail, it does not appear in the normal places on Marketing Cloud.

But there are some basic stats available at Email > Tracking > Tracking Reports > Triggered Sends tracking

Choose the definitionKey in the dropdown and you'll see bounces, opening rates, click rates, etc.
