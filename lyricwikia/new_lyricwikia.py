#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip3 install pprint')
from pprint import pprint


# In[2]:


get_ipython().system('pip3 install beautifulsoup4')


# In[3]:


get_ipython().system('pip3 install --upgrade pip')


# In[4]:


get_ipython().system('pip3 install requests')


# In[5]:


from six.moves.urllib.parse import quote as _quote
from bs4 import BeautifulSoup as _BeautifulSoup
import requests as _requests
import urllib
import os
import pandas as pd

__BASE_URL__ = 'https://lyrics.fandom.com'


# In[6]:


class LyricsNotFound(Exception):
    __module__ = Exception.__module__

    def __init__(self, message=None):
        super(LyricsNotFound, self).__init__(message)


# In[7]:


class LanguageNotFound(Exception):
    __module__ = Exception.__module__

    def __init__(self, message=None):
        super(LanguageNotFound, self).__init__(message)


# In[8]:


def urlize(string):
    """Convert string to LyricWikia format"""
    return _quote('_'.join(string.split()))


# In[9]:


def create_url(artist, song, language):
    """Create the URL in the LyricWikia format"""
    url = __BASE_URL__ + '/wiki/{artist}:{song}'.format(artist=urlize(artist), song=urlize(song))
    if language:
        url += '/{language}'.format(language=urlize(language).lower())
    return url


# In[10]:


def get_lyrics_for_all_languages(artist, song, linesep='\n', timeout=None):
    """Retrieve the lyrics of the song in all languages available"""
    url = create_url(artist, song, '')
    response = _requests.get(url, timeout=timeout)
    soup = _BeautifulSoup(response.content, "html.parser")
    lyricboxes = soup.find('table', {'class': 'banner banner-song'})
    result = dict()
    result['default'] = get_lyrics_by_language(artist, song, '', linesep='\n', timeout=None)
    
    for a in lyricboxes.findAll('a', href=True):
        result[a.getText()] = get_lyrics_by_language(artist, song, a['href'].split('/')[-1], linesep='\n', timeout=None)
    
    return result


# In[11]:


def get_lyrics_by_language(artist, song, language, linesep='\n', timeout=None):
    """Retrieve the lyrics of the song in a particular language and return the first one in case
    multiple versions are available."""
    return get_all_lyrics(artist, song, language, linesep, timeout)[0]


# In[12]:


def get_lyrics(artist, song, language='', linesep='\n', timeout=None):
    """Retrieve the lyrics of the song and return the first one in case
    multiple versions are available."""
    return get_all_lyrics(artist, song, language, linesep, timeout)[0]


# In[13]:



def get_all_lyrics(artist, song, language='', linesep=' \n ', timeout=None):
    """Retrieve a list of all the lyrics versions of a song."""
    url = create_url(artist, song, language)
    response = _requests.get(url, timeout=timeout)
    soup = _BeautifulSoup(response.content, "html.parser")
    lyricboxes = soup.findAll('div', {'class': 'lyricbox'})

    if not lyricboxes:
        raise LyricsNotFound('Cannot download lyrics')

    for lyricbox in lyricboxes:
        for br in lyricbox.findAll('br'):
            br.replace_with(linesep)

    return [lyricbox.text.strip() for lyricbox in lyricboxes]


# In[14]:


def get_songs_by_artist(artist, linesep=' \n ', timeout=None):
    """Retrieve a dataframe of all lyrics versions of a song."""
    df = pd.DataFrame(columns=['Artist', 'Title'])
    url = "https://lyrics.fandom.com/wiki/Category:Songs_by_"+urlize(artist)
    df = parse_page_now(url,df)
    return df


# In[15]:


def get_songs_by_language(language, linesep=' \n ', timeout=None):
    """Retrieve a dataframe of all lyrics versions of a song."""
    df = pd.DataFrame(columns=['Artist', 'Title'])
    url = "https://lyrics.fandom.com/wiki/Category:Language/"+language
    df = parse_page_now(url,df)
    return df


# In[16]:


def parse_page_now(url, df, timeout=None):
    response = _requests.get(url, timeout=timeout)
    soup = _BeautifulSoup(response.content, "html.parser")
    data = soup.findAll('li',attrs={'class':'category-page__member'})
    
    if not data:
        raise LanguageNotFound('No such artist')
    
    for div in data:
        links = div.findAll('a')
        for a in links:
            
            lyric_link = a['href'].strip('/wiki/')
            artist = lyric_link.split(":")[0]
            title = lyric_link.split(":")[1]
            if(artist == "Category"):
                continue
            df = df.append({'Artist': artist, 'Title': title}, ignore_index=True)
    
    if(soup.find('div', attrs={'class':'category-page__pagination'}) == None):
        return df

    next_page_text = soup.find('div', attrs={'class':'category-page__pagination'}).find('a', attrs={'class':'category-page__pagination-next wds-button wds-is-secondary'})
    if next_page_text != None:
        next_page_url = next_page_text['href']
        df = parse_page_now(next_page_url,df)
    return df


# In[17]:


def parse_page_now(url, df, timeout=None):
    response = _requests.get(url, timeout=timeout)
    soup = _BeautifulSoup(response.content, "html.parser")
    data = soup.findAll('li',attrs={'class':'category-page__member'})
    
    if not data:
        raise LanguageNotFound('No such language')
    
    for div in data:
        links = div.findAll('a')
        for a in links:
            
            lyric_link = a['href'].strip('/wiki/')
            artist = lyric_link.split(":")[0]
            title = lyric_link.split(":")[1]
            if(artist == "Category"):
                continue
            df = df.append({'Artist': artist, 'Title': title}, ignore_index=True)
    
    if(soup.find('div', attrs={'class':'category-page__pagination'}) == None):
        return df

    next_page_text = soup.find('div', attrs={'class':'category-page__pagination'}).find('a', attrs={'class':'category-page__pagination-next wds-button wds-is-secondary'})
    if next_page_text != None:
        next_page_url = next_page_text['href']
        df = parse_page_now(next_page_url,df)
    return df


# In[18]:


class Song(object):
    """A Song backed by the LyricWikia API"""

    def __init__(self, artist, title):
        self.artist = artist
        self.title = title

    @property
    def lyrics(self):
        """Song lyrics obtained by parsing the LyricWikia page"""
        return get_lyrics(self.artist, self.title,'')

    def __str__(self):
        return "Song(artist='%s', title='%s')" % (self.artist, self.title)

    def __repr__(self):
        return str(self)


# In[19]:


class Album(object):
    """An Album backed by the LyricWikia API"""

    def __init__(self, artist, album_data):
        self.artist = artist
        self.title = album_data['album']
        self.year = album_data['year']
        self.songs = [Song(artist, song) for song in album_data['songs']]

    def __str__(self):
        return "Album(artist='%s', title='%s')" % (self.artist, self.title)

    def __repr__(self):
        return str(self)


# In[20]:



class Artist(object):
    """An Artist backed by the LyricWikia API"""

    __API__ = __BASE_URL__ + '/api.php?fmt=json&func=getArtist&artist={artist}'

    def __init__(self, name):
        url = self.__API__.format(artist=urlize(name))
        data = _requests.get(url).json()
        self.name = data['artist']
        self.albums = [Album(self.name, album) for album in data['albums']]

    def __str__(self):
        return "Artist(name='%s')" % (self.name)

    def __repr__(self):
        return str(self)


# In[21]:


artist_name = "Mondstille"
df = pd.DataFrame(columns=['Artist', 'Title'])
url = "https://lyrics.fandom.com/wiki/Category:Songs_by_"+artist_name
df = parse_page_now(url,df)


# In[22]:


get_songs_by_artist("Mondstille")


# In[26]:


get_lyrics_by_language("PSY", "Gangnam Style", "roman")

