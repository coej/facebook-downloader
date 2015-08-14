#!/usr/bin/env python

# Python 2/3 compatibility
from __future__ import (print_function, unicode_literals, division)
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

__metaclass__ = type


import os
import requests
import json
import time
from datetime import datetime
import pymongo



from enum import Enum
class Nodes(Enum):
    post = 'post' # Nodes.post
    like = 'like' # Nodes.like
    comment = 'comment' # Nodes.comment
    reply = 'reply'
    insights_metric = 'insights_metric' #Nodes.insights_metric



class Data_Page:
    def __init__(self, connection, data, item_types):
        from datetime import datetime

        self.item_types = item_types
        self.data = data['data']
        try:
            paging = data['paging']
        except KeyError:
            self.next_page_url = None
            self.last_page_url = None
            raise StopIteration
        self.next_page_url = paging['next'] if 'next' in paging else None
        self.prev_page_url = paging['previous'] if 'previous' in paging else None    
        self.items = []
        for item in self.data:
            if item_types == Nodes.post:
                p = Post(connection, item)
                p.data['total_likes_count'] = connection.get_likes_count(p)
                p.data['total_comments_count'] = connection.get_comments_count(p)

            elif item_types == Nodes.like:
                p = Like(connection, item)
            elif item_types == Nodes.comment:
                p = Comment(connection, item)
            elif item_types == Nodes.reply:
                p = Comment(connection, item) ## change later?
            elif item_types == Nodes.insights_metric:
                p = Insights_Metric(connection, item)
            else:
                raise ValueError(item)

            p.data['downloaded_time'] = datetime.now()
            self.items.append(p)

    
class Post:
    def __repr__(self):
        if len(str(self.data)) > 100:
            return 'Post() %s (...) \n' % self.data[:100]
        else:
            return 'Post() %s \n' % self.data
    def __str__(self):
        return self.data
    def __init__(self, connection, data):
        self.data = data
        self.post_type = data['type']
        try:
            self.likes_p1 = Data_Page(connection, data['likes'], item_types=Nodes.like)
        except KeyError:
            self.likes_p1 = None
        try:
            self.comments_p1 = Data_Page(connection, data['comments'], item_types=Nodes.comment)
        except KeyError:
            self.comments_p1 = None


# class Summary:
    # json groups are "data", "paging", and sometimes "summary"
    # e.g., when you request 5647744585_10151775853479586/likes?summary=true

class Like:
    def __repr__(self):
        return 'Like(): %s \n' % self.data
    def __init__(self, connection, data):
        self.data = data
        self.item_type = Nodes.like

class Comment:
    def __repr__(self):
        return 'Comment(): %s \n' % self.data
    def __init__(self, connection, data):
        self.data = data
        self._id = data['id']
        self.item_type = Nodes.comment

class Insights_Metric:
    def __repr__(self):
        return 'Comment(): %s \n' % self.data
    def __init__(self, connection, data):
        self.data = data
        self._id = data['id']
        self.item_type = Nodes.insights_metric



class FacebookConnection:

    def __init__(self, token=None):
        self.token = token
        self.update_token()


    def token_is_current(self):
        r = self.query(node='me', edge=None, fields=None, 
                             query_params=None, pass_errors=True)
        #print (r)
        if 'error' in r:
            if r['error']['type'] == 'OAuthException':
                return False
            else:
                raise ValueError(r['error'])
        else:
            return True


    def update_token(self):
        def token_browser_input():
            import webbrowser
            webbrowser.open_new_tab("https://developers.facebook.com/tools/explorer/")
            from builtins import input
            self.token = input('token: ')
        
        while not self.token_is_current():
            print ("Opening browser to fetch a new token.")
            token_browser_input()
            #print (self.token)
        #print ('finished while loop. self.token:')
        #print (self.token)
        print ("Token validated for basic user-level access.")
        return True


    def query_url(self, node, edge=None, query_params=None, 
                       fields=None):
        import urllib
        import requests
        from urllib.parse import urlencode

        root = 'https://graph.facebook.com/v2.3'
        if not edge: edge = ''

        param_kwargs = {'access_token': self.token}

        if fields:
            field_list_str = ','.join(fields)
            param_kwargs['fields'] = field_list_str
        if query_params:
            param_kwargs.update(query_params)
        param_string = urlencode(param_kwargs)

        url = '{root}/{node}/{edge}?{params}'.format(
            root=root, node=node, edge=edge, params=param_string)
        return url


    def query(self, node, edge=None, query_params=None, 
              fields=None, print_url=False, pass_errors=False):
        url = self.query_url(node, edge, query_params, fields)
        if print_url:
            print (url)
        return getj(url, pass_errors)


    def get_likes_count(self, post_obj):
        post_id = post_obj.data['id']
        res = self.query(node=post_id, edge='likes',
                         query_params={'summary':'true'})
        try:
            likes = int(res['summary']['total_count'])
            return likes
        except:
            print ("[!likes]")
            return None


    def get_comments_count(self, post_obj):
        post_id = post_obj.data['id']
        res = self.query(node=post_id, edge='comments',
                         query_params={'summary':'true'})
        try:
            likes = int(res['summary']['total_count'])
            return likes
        except:
            print ("[!comments]")
            return None


    def get_post_insights(self, post_id, show_progress=False):

        # we'll have to change this later to work as an update to our post collection
        # rather than creating new keys on each post ID in a new collection...
        response = self.query(node='{}/insights'.format(post_id),
                                  edge=None,
                                  query_params=None,
                                  fields=None,
                                  print_url=False)

        metrics_firstpage = Data_Page(self, response, Nodes.insights_metric)
        generator = facebook_paging(self, metrics_firstpage, 
                                    show_progress=False, #don't want one tick for each metric
                                    print_urls=False,
                                    first_page_only=True)

        metric_list = list(generator)

        #then, add extras:
        insights_block = {'_id': post_id}
        for m in metric_list:
            insights_block[m['name']] = m
        #insights_block['like_count'] = get_like_count(post_id)
        #insights_block['share_count'] = get_share_count(post_id)

        return insights_block



def downloader(collection,  # pymongo collection object
               account_id,  # facebook account node
               token, 
               since,       # string, e.g., 2015-01-01
               until,       # string, e.g., 2015-03-31
               skip_duplicates=True, 
               silent=False):

    import json
    import time
    from datetime import datetime
    import pymongo

    fb = FacebookConnection(token)

    response = fb.query(node=account_id,
                        edge='posts',
                        query_params={'since': since,
                                      'until': until,
                                      },
                        fields=None,
                        print_url=False)

    posts_firstpage = Data_Page(fb, response, Nodes.post)
    generator = facebook_paging(fb, posts_firstpage, 
                                show_progress=True)

    for post in generator:

        post['insights'] = fb.get_post_insights(post['id'])

        post = post_transformations(post)

        try:
            wresult = collection.insert(post) #, upsert=True) --> for .update()
            if not silent:
                print('.', end='')
        except pymongo.errors.DuplicateKeyError:
            if skip_duplicates and not silent: 
                print('d', end='')
            else: raise
        except pymongo.errors.InvalidDocument:
            print ('invalid: %s' % post['_id'])
            raise
        except:
            raise
        time.sleep(.1)


def printj(data): 
    print (json.dumps(data, indent=1))
    

def replace_dot_key(obj):
    # Necessary if saving JSON keys with periods in them into a MongoDB document
    # (periods aren't allowed).
    # use as:
    # new_json = json.loads(data, object_hook=remove_dot_key)     
    for key in obj.keys():
        new_key = key.replace(".","_DOT_")
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj


def getj(url, pass_errors=False): 
    #print url
    #response_json = requests.get(url).json()

    try:
        response_text = requests.get(url).text
    except:
        print (url)
        raise
    try:
        # can't load JSON objects with a '.' in any key
        # into MongoDB.
        response_json = json.loads(response_text, 
                                   object_hook=replace_dot_key) 
    except:
        print (response_json)
        raise    
    if 'error' in response_json and not pass_errors:
        raise ValueError(response_json['error'])
    return response_json


def post_transformations(post):
    
    def parse_fb_datetime(datetime_string):
        from datetime import datetime
        return datetime.strptime(datetime_string,'%Y-%m-%dT%H:%M:%S+0000')

    post['_id'] = post['id']
    # del post['id']    
    post['created_datetime'] = parse_fb_datetime(post['created_time'])
    post['updated_datetime'] = parse_fb_datetime(post['updated_time'])
    return post
       

def facebook_paging(connection, data_page_one, show_progress=True, print_urls=False,
                    first_page_only=False):
    import time

    progress_mark = {
        Nodes.comment: 'xC ',
        Nodes.like: 'xL ',
        Nodes.post: 'xP ',
        Nodes.reply: 'xc ',
        Nodes.insights_metric: 'xI '
    }        

    # determine whether we're looking at a page of posts, comments, etc.
    item_types = data_page_one.item_types
    
    next_page = data_page_one
    while True:
        # don't yield the whole page-- pass out elements
        #yield next_page
        current_page_items = next_page.data
        for item in current_page_items:
            yield item
            #f item_types = Node.page:
            #   yield item
        
        time.sleep(.1)
        if show_progress:
            print(len(current_page_items), end='')
            try:
                print(progress_mark[item_types], end='')
            except KeyError:
                print('?')

        if first_page_only:
            break
        last_page = next_page        
        next_url = last_page.next_page_url
        if print_urls:
            print ('\n' + next_url + '\n')

        response = getj(next_url)
        try:
            next_page = Data_Page(connection, response, item_types=item_types)
        except StopIteration:
            break

        # other cases that mean we're out of data pages
        if next_page.next_page_url == last_page.next_page_url:
            break
        elif not next_page.next_page_url:
            break
        elif next_page.data == last_page.data:
            break

    if show_progress:
        print('| ', end='')


def insight_value(post,name):
    insight_node = post['insights'][name]
    value = insight_node['values'][0]['value']
    return value


def fb_month_range(year, month):
    import calendar, datetime
    one_day = datetime.timedelta(days=1)
    first_weekday, length = calendar.monthrange(year, month)
    start = str(datetime.date(year,month,1))
    end = str(datetime.date(year,month,length) + one_day) # FB API uses midnight-before-this-day as cutoff for "until"
    return (start, end)

       
