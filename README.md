# facebook_downloader
Downloads the full history of Facebook post data and analytics ("insights") to a local database. 

Limitations:
* MongoDB only for now via PyMongo. Postgres support to be added next.
* Tested only on organization pages (doesn't work on personal accounts yet).
* Fields aren't processed nicely yet (e.g., some data data is saved as strings instead of DateTime)

Usage example:
```Python
from facebookapi_wrapper import facebook_downloader, FacebookConnection

import pymongo
client = pymongo.MongoClient('mongodb://localhost:27017/')
print (client)
db = client['facebook_db']
print (db.posts_myorganizationpage)

# optional token entry: will automatically open a browser window
# to retrieve a short-term token from the Graph API Explorer if needed
token = 'CAACEdEose0c...'
fb = FacebookConnection(token)

# testing connection
auth_list = fb.query(node='me', edge='accounts') 

# get 60-day tokens for organizational accounts you have access to
tokens = {acct['name']: acct['access_token'] for acct in auth_list['data']}
print(tokens)

token_org1 = tokens['long name of organization number one']
token_org2 = tokens['long name of organization number two']

# account = the node ID of the page you're accessing (as seen in Facebook urls)
# either numeric or friendly ID works
for (account, acct_token) in [('myorgpage', token_org1), 
                              ('someotherorg', token_org2)]:
    
    account_coll = db['posts_' + account.replace('.','')]
    print('\n', account_coll)
    print(acct_token)

    facebook_downloader(collection=account_coll, 
                        account_id=account, 
                        token=acct_token, 
                        since='2015-01-01', 
                        until='2015-07-01', 
                        skip_duplicates=True, 
                        silent=False)
```
