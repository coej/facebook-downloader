# facebook-downloader
Downloads the full history of Facebook post data and analytics ("insights") to a local database. 

Limitations:
* Downloads to MongoDB only for now, via PyMongo. PostgresQL support to be added next.
* Can't update individual post documents already in MongoDB (but can ignore duplicate post IDs).
* Tested only on organization pages (doesn't work on personal accounts yet).
* Fields aren't all saved as correct types (e.g., some date fields are saved as strings).
* Post comments aren't saved except for comments included in the first page of API results (requires crawling through pages of comments returned by the API).

FacebookConnection().query() and get_post_insights() also provide more general-purpose Facebook Graph API interfaces.

Usage example:
```Python
from facebook_downloader import downloader, FacebookConnection

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

    downloader(collection=account_coll,  # pymongo collection object
               account_id=account,       # facebook account node
               token=acct_token,
               since='2015-01-01',       # string, e.g., '2015-01-01'
               until='2015-07-01',       # string, e.g., '2015-03-31'
               skip_duplicates=True, 
               silent=False)
```
