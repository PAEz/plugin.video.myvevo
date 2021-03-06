# -*- coding: utf-8 -*-
# KodiAddon for myVEVO
#
from t1mlib import t1mAddon
import json
import re
import urllib
import urllib2
import cookielib
import xbmcplugin
import xbmcgui
import xbmc
import sys
import os
import HTMLParser

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
qp  = urllib.quote_plus
UTF8 = 'utf-8'
VEVOAPI = 'https://apiv2.vevo.com'

class myAddon(t1mAddon):

  def getAutho(self, getMe=False):
      if self.addon.getSetting('login_name') != '':
          vevoName = self.addon.getSetting('login_name')
          vevoPswd = self.addon.getSetting('login_pass')
          udata = urllib.urlencode({'username': vevoName, 'password':vevoPswd, 'grant_type':'password', 'client_id':'SPupX1tvqFEopQ1YS6SS'})
      else:
          udata = ' '
      uheaders = self.defaultHeaders.copy()
      uheaders['X-Requested-With'] = 'XMLHttpRequest'
      uheaders['Connection'] = 'keep-alive'
      html  = self.getRequest('https://accounts.vevo.com/token', udata , uheaders)
      try:
          a = json.loads(html)
      except:
          if not getMe:
              return(None)
          else:
              return(None,None)
      if not getMe:
          return a.get('legacy_token')
      uheaders['Authorization'] = 'Bearer %s' % a['access_token']
      html = self.getRequest('https://users.vevo.com/user/me', None, uheaders)
      b = json.loads(html)
      return (a['legacy_token'], b.get('vevo_user_id'))


  def getAPI(self,url):
      autho = self.getAutho()
      uheaders = self.defaultHeaders.copy()
      uheaders['Authorization'] = 'Bearer %s' % autho
      uheaders['Connection'] = 'keep-alive'
      html = self.getRequest(url, None , uheaders)
      return json.loads(html)


  def getAddonMenu(self,url,ilist):
      addonLanguage = self.addon.getLocalizedString
      menu = [('Genres', 'https://www.vevo.com/genres', 'GC'),
              ('Trending Now','https://www.vevo.com/trending-now?page=1','GC'),
              ('Recently Added','https://www.vevo.com/recently-added?page=1','GC'),
              ('Popular Artists','https://www.vevo.com/artists?page=1','GC'),
              ('Search','Search', 'GE'),
              ('Favorite Artists','GM', 'GM')]
      a = self.getAutho()
      if not a is None:
          menu.append((addonLanguage(30003),'GS','GS'))

      for name, url, mode in menu:
          ilist = self.addMenuItem(name, mode, ilist, url, self.addonIcon, self.addonFanart, None, isFolder=True)
      return(ilist)


  def getAddonCats(self,url,ilist):
      addonLanguage = self.addon.getLocalizedString
      contextMenu = []
      html = self.getRequest(url)
      if '/playlist/' in url:
          feedItems = re.compile('<div class="link-container"(.+?)<span class="share-label">', re.DOTALL).findall(html)
      else:
          feedItems= re.compile('<li class="feedV2-item(.+?)</li>', re.DOTALL).findall(html)
          if feedItems == []:
              feedItems= re.compile('<div class="feedV2-item(.+?)<div class="modal-container"', re.DOTALL).findall(html)
      for item in feedItems:
          if ('/artist/' in url):
              (iUrl,image,name) = re.compile('href="(.+?)".+?srcSet="(.+?)".+?class="feed-item-title">(.+?)<', re.DOTALL).search(item).groups()
          elif ('/playlist/' in url):
              (image,name) = re.compile('srcSet="(.+?)".+?class="artist"><span>(.+?)<', re.DOTALL).search(item).groups()
              iUrl = image.split('/thumb/video/',1)[1]
              iUrl = iUrl.split('/',1)[0]
          else:
              (image,iUrl,name) = re.compile('srcSet="(.+?)".+?class="feed-item-title" href="(.+?)">(.+?)<', re.DOTALL).search(item).groups()
          name = h.unescape(name.decode(UTF8))
          infoList = {}
          if iUrl.startswith('/genres/'):
              mode = 'GS'
              name = name.upper()
          elif (('?page=' in url) or ('/artist/' in url) or ('/playlist/' in url)) and (not ('/popular-artists' in url) and not ('/playlists' in url) and not ('/artists' in url)):
              mode = 'GV'
              infoList['Artist'] = name.split('&')
#              (iUrl, title) = re.compile('<a class="feed-item-subtitle" href="(.+?)">(.+?)</',re.DOTALL).search(item).groups()
              if ('/artist/' in url):
                  title = re.compile('class="feed-item-subtitle">(.+?)</',re.DOTALL).search(item).group(1)
              elif ('/playlist/' in url):
                  title = re.compile('class="video-name">(.+?)</',re.DOTALL).search(item).group(1)
              else:
                  (iUrl, title) = re.compile('class="feed-item-subtitle" href="(.+?)">(.+?)</',re.DOTALL).search(item).groups()
              title = h.unescape(title.decode(UTF8))
              title = title.replace('<h3>','',1)
              infoList['Plot'] = '"%s" by %s' % (title, name)
              name = title
              infoList['mediatype'] = 'musicvideo'
              contextMenu = [(addonLanguage(30013),'XBMC.RunPlugin(%s?mode=DF&url=AP%s)' % (sys.argv[0],'https://www.vevo.com' + iUrl)),
                             (addonLanguage(30012),'XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0],'https://www.vevo.com' + iUrl))]
          else:
              mode = 'GC'
          infoList['Title'] = name
          if not '/playlist/' in url:
               iUrl = 'https://www.vevo.com' + iUrl
          image = 'https:' + image
          ilist = self.addMenuItem(name, mode, ilist, iUrl, image, image, infoList, isFolder=(not(mode == 'GV')), cm=contextMenu )


      nextPTR = re.compile('<div class="page">(.+?)</div><a class="next page-button" rel="next" href="(.+?)">next</a>', re.DOTALL).search(html)

      if nextPTR is not None:
          (pageName, nextUrl) = nextPTR.groups()
          nextUrl = 'https://www.vevo.com' + nextUrl
          pageName = '[COLOR blue]'+pageName+' '+addonLanguage(30005)+'[/COLOR]'
          ilist = self.addMenuItem(pageName, 'GC', ilist, nextUrl, self.addonIcon, self.addonFanart, infoList,isFolder=True )
      return(ilist)


  def updateList(self, token = None, pid = None, cmd = None, name = None, desc = None, isrc = None, imageUrl = None):
      addonLanguage = self.addon.getLocalizedString
      MAXPLISTITEMS = 25
      if token is None:
          token = self.getAutho()
      html = self.getRequest(VEVOAPI + ('/playlist/%s?token=%s' % (pid, token)))
      a = json.loads(html)
      ud = 'playlistId=%s' % qp(pid)
      if name is None:
          name = a['name']
      ud += '&name=%s' % qp(name)
      if desc is None:
          desc = a.get('description')
      if desc is not None:
          ud += "&description=%s" % qp(desc)
      if imageUrl is None:
          imageUrl = a.get('imageUrl')
      if imageUrl is not None:
          ud += "&imageUrl=%s" % qp(imageUrl)
      b = a["videos"]
      if (cmd == 'ADDITEM') and (len(b) >= MAXPLISTITEMS):
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( 'VEVO', addonLanguage(30006), 5000) )
          return                 
      for c in b:
          if (cmd == 'DELITEM') and (c['isrc'] == isrc):
              continue
          else:
              ud += "&Isrcs=%s" % qp(c['isrc'])
      if cmd == 'ADDITEM':
          ud += "&Isrcs=%s" % qp(isrc)
      azheaders = self.defaultHeaders.copy()
      azheaders['X-Requested-With'] = 'XMLHttpRequest'
      url = VEVOAPI + ('/me/playlist/%s?token=%s' % (pid, token))
      html  = self.getRequest(url, ud , azheaders, rmethod = 'PUT')
      return


  def getAddonShows(self,url,ilist):
      if url.startswith('http'):
          image = xbmc.getInfoLabel('ListItem.Art(thumb)')
          sList = [('Trending Now', '/trending-videos'), ('Recently Added','/recently-added'), ('Popular Artists','/popular-artists')]
          for (name, sUrl) in sList:
              iUrl = url+sUrl+'?page=1'
              ilist = self.addMenuItem(name, 'GC', ilist, iUrl, image, image, {}, isFolder=True)          
          return(ilist)
      addonLanguage = self.addon.getLocalizedString
      token, uid = self.getAutho(getMe = True)
      if token == None:
          return(ilist)
      pid = url[2:]
      func = url[:2]
      uheaders = self.defaultHeaders
      uheaders['X-Requested-With'] = 'XMLHttpRequest'
      if func == 'DP':
          url = VEVOAPI + ('/me/playlist/%s?token=%s') % (pid, token)
          html = self.getRequest(url, ' ', uheaders, rmethod='DELETE')
      elif func == 'RL':
          html = self.getRequest(VEVOAPI + ('/playlist/%s?token=%s' % (pid, token)))
          a = json.loads(html)
          oldname = a["name"]
          keyb = xbmc.Keyboard(oldname, addonLanguage(30007))
          keyb.doModal()
          if (keyb.isConfirmed()):
              newname = keyb.getText()
              if len(newname) > 0: 
                  self.updateList(token = token, pid = pid, cmd = 'REN', name=newname)
      elif func == 'CP':
          keyb = xbmc.Keyboard('', addonLanguage(30008))
          keyb.doModal()
          if (keyb.isConfirmed()):
              text = keyb.getText()
              udata = 'name=%s&Isrcs=undefined' % qp(text)
              url = VEVOAPI + ('/me/playlists?token=%s' % token)
              self.getRequest(url, udata, uheaders)
      xbmcplugin.setContent(int(sys.argv[1]), 'files')
      html = self.getRequest(VEVOAPI + ('/user/%s/playlists?token=%s' % (uid,token)))
      a = json.loads(html)
      for b in a:
          thumb = b.get("thumbnailUrl")
          name = b["name"]
          url = 'GL' + VEVOAPI + '/playlist/%s?token=' % b["playlistId"]
          infoList ={}
          infoList['Title'] = name
          infoList['Plot'] = b.get("description")
          contextMenu = [(addonLanguage(30009),'XBMC.Container.Refresh(%s?mode=GS&url=DP%s)' % (sys.argv[0], b["playlistId"])),
                         (addonLanguage(30010),'XBMC.Container.Refresh(%s?mode=GS&url=RL%s)' % (sys.argv[0], b["playlistId"]))]
          ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True, cm=contextMenu)
      ilist = self.addMenuItem('[COLOR blue]'+addonLanguage(30015)+'[/COLOR]', 'GS', ilist, 'CP' , self.addonIcon, self.addonFanart, None, isFolder=True)
      return(ilist)




  def getAddonEpisodes(self,url,ilist):
      addonLanguage = self.addon.getLocalizedString
      url = uqp(url)
      self.defaultVidStream['width']  = 1920
      self.defaultVidStream['height'] = 1080
      xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
      playList = None
      if url == 'Search':
          keyb = xbmc.Keyboard('', addonLanguage(30004))
          keyb.doModal()
          if (keyb.isConfirmed()):
#              url = 'https://apiv2.vevo.com/search?page=1&size=50&q=' + keyb.getText().replace(' ','+')
              url = 'https://quest.vevo.com/search?page=1&size=50&q=' + keyb.getText().replace(' ','+')
          else:
              return(ilist)
      elif url.startswith('GF'):
#          url = 'https://apiv2.vevo.com/search?artistsLimit=1&page=1&size=50&skippedVideos=0&q=' + url[2:]
#          url = 'https://apiv2.vevo.com/search?artistsLimit=1&page=1&size=50&skippedVideos=0&q=' + url[2:].replace(' ','+')
          url = 'https://quest.vevo.com/search?artistsLimit=1&page=1&size=50&skippedVideos=0&q=' + url[2:].replace(' ','+')
      elif url.startswith('GL'):
          url = url[2:]
          playList = re.compile('\/playlist\/(.+?)\?', re.DOTALL).search(url).group(1)
      if url.endswith('token='):
          url += self.getAutho()
      if not url.startswith('http'):
          url = 'https://apiv2.vevo.com' + url
#      a = self.getAPI(url)
      html = self.getRequest(url)
      a = json.loads(html)
      nextUrl = None
      if type(a) is not list:
          nextUrl = a.get('paging')
          if nextUrl is not None:
              nextUrl = nextUrl.get('next')
      if type(a) is list:
          if a[0].get('stream') is not None:
              akeys = ['name', 'stream', 'thumbnailUrl']
          else:
              akeys = ['title', 'isrc', 'thumbnailUrl']
      elif a.get('videos') is not None:
          a = a['videos']
          akeys = ['title', 'isrc', 'thumbnailUrl']
      elif a.get('nowPosts') is not None:
          a = a['nowPosts']
          akeys = ['name', 'isrc', 'image']
      lastUrl = None
      for b in a:
          if b is None:
              continue
          playlistId = b.get('playlistId')
          if playlistId is None:
              url = b.get(akeys[1]) #isrc
              url = 'https://www.vevo.com/watch/%s/%s/%s' % (b['artists'][0].get('urlSafeName'),b.get('urlSafeTitle'),b.get('isrc'))
          else:
              url = '/playlist/%s?token=' % playlistId
          if url is None or url == lastUrl:
              continue
          lastUrl = url
          name = b[akeys[0]]
          thumb = b.get(akeys[2])
          if thumb is None:
              thumb = b.get('images')
              if thumb is not None: 
                  thumb = thumb[0].get('image')
          infoList = {}
          infoList['Title'] = name
#          infoList['Plot'] = b.get('description')
          artists = b.get('artists')
          infoList['Artist'] = [] 
          if artists is not None and artists != []:
              for artist in artists:
                  infoList['Artist'].append(artist['name'] + ' ')
          else:
              if name.endswith('"') and akeys[2] == 'image':
                  artist, name = name.split('"',1)
                  infoList['Artist'].append(artist.strip())
                  name = name.strip('"').strip()
                  infoList['Title'] = name             
              else:
                  infoList['Artist'].append(xbmc.getInfoLabel('ListItem.Artist'))
          infoList['Plot'] = '"%s" by %s' % (name, infoList.get("Artist",[''])[0])
          vyear = b.get('year')
          if vyear is not None and vyear != 0:
              infoList['Year'] = vyear
          infoList['duration'] = b.get('duration')
          infoList['mediatype']= 'musicvideo'
          if playList is not None:
              contextMenu = [(addonLanguage(30011),'XBMC.Container.Update(%s?mode=DF&url=DP%spid%s)' % (sys.argv[0],url, playList)),
                             (addonLanguage(30012),'XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0],url))]
          else:
              contextMenu = [(addonLanguage(30013),'XBMC.RunPlugin(%s?mode=DF&url=AP%s)' % (sys.argv[0],url)),
                             (addonLanguage(30012),'XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0],url))]
          if akeys[1] == 'isrc':
              curl = VEVOAPI + ('/video/%s/related?&page=1&size=50&token=' % (url))
              contextMenu.append((addonLanguage(30014),'XBMC.Container.Update(%s?mode=GE&url=%s)' % (sys.argv[0],qp(curl))))
          if playlistId is None:
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, thumb, infoList, isFolder=False, cm=contextMenu)
          else:
              contextMenu = []
              name = '[COLOR yellow]'+name+'[/COLOR]'
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, thumb, infoList, isFolder=True, cm=contextMenu)

      if nextUrl is not None:
          name = '[COLOR blue]'+addonLanguage(30005)+'[/COLOR]'
          ilist = self.addMenuItem(name, 'GE', ilist, nextUrl, self.addonIcon, self.addonFanart, [], isFolder=True)
      return(ilist)


  def getAddonMovies(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
      json_cmd= '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "limits": { "start" : 0 }, "properties": [ "thumbnail", "fanart", "genre" ], "sort": { "order": "ascending", "method": "artist", "ignorearticle": true }}, "id": 1}'
      jsonRespond = xbmc.executeJSONRPC(json_cmd)
      a = json.loads(jsonRespond)
      for b in a["result"]["artists"]:
          name = b["artist"].encode(UTF8)
          thumb = b.get("thumbnail", self.addonIcon)
          fanart = b.get("fanart", self.addonFanart)
          url = 'GF'+name.replace(' ','+')
          infoList = {}
          infoList['Title'] = name
          infoList['Plot'] = b.get('description')
          infoList['Artist'] = [name]
          vyear = b.get('year')
          if vyear is not None and vyear != 0:
              infoList['Year'] = vyear
          infoList['duration'] = b.get('duration')
          infoList['mediatype']= 'musicvideo'
          ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def doFunction(self, url):
      func = url[0:2]
      url = url[2:]
      if func == 'DP':
          isrc, pid = url.split('pid',1)
          self.updateList(pid = pid, token = None, cmd = 'DELITEM', isrc = isrc)
      elif func == 'AP':
          token, uid = self.getAutho(getMe = True)
          html = self.getRequest(VEVOAPI + ('/user/%s/playlists?token=%s' % (uid,token)))
          a = json.loads(html)
          ilist=[]
          nlist=[]
          for b in a:
              nlist.append(b['name'])
              ilist.append(b['playlistId'])
          dialog = xbmcgui.Dialog()
          choice = dialog.select('Choose a playlist', nlist)
          pid = ilist[choice]
          self.updateList(pid = pid, token = token, cmd = 'ADDITEM', isrc = url)
      elif func == 'AL':
          artist = xbmc.getInfoLabel('ListItem.Artist').split('/',1)[0]
          artist = artist.replace(':','').replace('-','').replace('?','%3F')
          title = xbmc.getInfoLabel('ListItem.Title').split('(',1)[0]
          title = title.replace(':','').replace('-','').replace('?','%3F')
          name = artist.strip() + ' - ' + title.strip()
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          videosDir  = xbmc.translatePath(os.path.join(profile,'Videos'))
          videoDir  = xbmc.translatePath(os.path.join(videosDir, name))
          if not os.path.isdir(videoDir):
              os.makedirs(videoDir)
          strmFile = xbmc.translatePath(os.path.join(videoDir, name+'.strm'))
          with open(strmFile, 'w') as outfile:
              outfile.write('%s?mode=GV&url=%s' %(sys.argv[0], url))
          json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % videoDir.replace('\\','/')
          jsonRespond = xbmc.executeJSONRPC(json_cmd)


  def getAddonVideo(self,url):
      if not (url.endswith('.m3u8') or url.endswith('.mp4')):
          if ('/' in url):
              html = self.getRequest(url)
              url = re.compile('\.streamsV3\.4"\:\{"quality"\:null,"url"\:"(.+?)"', re.DOTALL).search(html)
              if not url is None:
                  url = url.group(1)
              else:
                  url = re.compile('\.streamsV3\.7"\:\{"quality"\:null,"url"\:"(.+?)"', re.DOTALL).search(html)
                  if not url is None:
                      url = url.group(1)
                  else:
                      return
          else:
              url = ('https://apiv2.vevo.com/video/%s/streams/mpd?token=%s' % (url, self.getAutho()))
              a = self.getAPI(url)
              for b in a:
                  url = b.get('url')
                  if not url is None:
                      break
      thumb = xbmc.getInfoLabel('ListItem.Art(thumb)')
      liz = xbmcgui.ListItem(path = url, thumbnailImage = thumb)
      infoList ={}
      infoList['Artist'] = []
      infoList['Artist'].append(xbmc.getInfoLabel('ListItem.Artist'))
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      vyear = xbmc.getInfoLabel('ListItem.Year')
      if vyear is not None and vyear != 0:
          infoList['Year'] = vyear
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Album'] = xbmc.getInfoLabel('ListItem.Album')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['mediatype']= 'musicvideo'
      liz.setInfo('video', infoList)
      if url.endswith('.mpd'):
          liz.setProperty('inputstreamaddon','inputstream.adaptive')
          liz.setProperty('inputstream.adaptive.manifest_type','mpd')
      elif url.endswith('.m3u8'):
          liz.setProperty('inputstreamaddon','inputstream.adaptive')
          liz.setProperty('inputstream.adaptive.manifest_type','hls')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
