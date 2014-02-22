# encoding: utf-8

from __future__ import unicode_literals

import os
import re
import xml.etree.ElementTree

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    compat_xml_parse_error,

    ExtractorError,
    HEADRequest,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    url_basename,
)
from .brightcove import BrightcoveIE
from .ooyala import OoyalaIE


class GenericIE(InfoExtractor):
    IE_DESC = 'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = 'generic'
    _TESTS = [
        {
            'url': 'http://www.hodiho.fr/2013/02/regis-plante-sa-jeep.html',
            'file': '13601338388002.mp4',
            'md5': '6e15c93721d7ec9e9ca3fdbf07982cfd',
            'info_dict': {
                'uploader': 'www.hodiho.fr',
                'title': 'R\u00e9gis plante sa Jeep',
            }
        },
        # bandcamp page with custom domain
        {
            'add_ie': ['Bandcamp'],
            'url': 'http://bronyrock.com/track/the-pony-mash',
            'file': '3235767654.mp3',
            'info_dict': {
                'title': 'The Pony Mash',
                'uploader': 'M_Pallante',
            },
            'skip': 'There is a limit of 200 free downloads / month for the test song',
        },
        # embedded brightcove video
        # it also tests brightcove videos that need to set the 'Referer' in the
        # http requests
        {
            'add_ie': ['Brightcove'],
            'url': 'http://www.bfmtv.com/video/bfmbusiness/cours-bourse/cours-bourse-l-analyse-technique-154522/',
            'info_dict': {
                'id': '2765128793001',
                'ext': 'mp4',
                'title': 'Le cours de bourse : l’analyse technique',
                'description': 'md5:7e9ad046e968cb2d1114004aba466fd9',
                'uploader': 'BFM BUSINESS',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # https://github.com/rg3/youtube-dl/issues/2253
            'url': 'http://bcove.me/i6nfkrc3',
            'file': '3101154703001.mp4',
            'md5': '0ba9446db037002366bab3b3eb30c88c',
            'info_dict': {
                'title': 'Still no power',
                'uploader': 'thestar.com',
                'description': 'Mississauga resident David Farmer is still out of power as a result of the ice storm a month ago. To keep the house warm, Farmer cuts wood from his property for a wood burning stove downstairs.',
            },
            'add_ie': ['Brightcove'],
        },
        # Direct link to a video
        {
            'url': 'http://media.w3.org/2010/05/sintel/trailer.mp4',
            'file': 'trailer.mp4',
            'md5': '67d406c2bcb6af27fa886f31aa934bbe',
            'info_dict': {
                'id': 'trailer',
                'title': 'trailer',
                'upload_date': '20100513',
            }
        },
        # ooyala video
        {
            'url': 'http://www.rollingstone.com/music/videos/norwegian-dj-cashmere-cat-goes-spartan-on-with-me-premiere-20131219',
            'file': 'BwY2RxaTrTkslxOfcan0UCf0YqyvWysJ.mp4',
            'md5': '5644c6ca5d5782c1d0d350dad9bd840c',
            'info_dict': {
                'id': 'BwY2RxaTrTkslxOfcan0UCf0YqyvWysJ',
                'ext': 'mp4',
                'title': '2cc213299525360.mov',  # that's what we get
            },
        },
    ]

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        if not self._downloader.params.get('test', False):
            self._downloader.report_warning('Falling back on generic information extractor.')
        super(GenericIE, self).report_download_webpage(video_id)

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)

    def _send_head(self, url):
        """Check if it is a redirect, like url shorteners, in case return the new url."""

        class HEADRedirectHandler(compat_urllib_request.HTTPRedirectHandler):
            """
            Subclass the HTTPRedirectHandler to make it use our
            HEADRequest also on the redirected URL
            """
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if code in (301, 302, 303, 307):
                    newurl = newurl.replace(' ', '%20')
                    newheaders = dict((k,v) for k,v in req.headers.items()
                                      if k.lower() not in ("content-length", "content-type"))
                    return HEADRequest(newurl,
                                       headers=newheaders,
                                       origin_req_host=req.get_origin_req_host(),
                                       unverifiable=True)
                else:
                    raise compat_urllib_error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        class HTTPMethodFallback(compat_urllib_request.BaseHandler):
            """
            Fallback to GET if HEAD is not allowed (405 HTTP error)
            """
            def http_error_405(self, req, fp, code, msg, headers):
                fp.read()
                fp.close()

                newheaders = dict((k,v) for k,v in req.headers.items()
                                  if k.lower() not in ("content-length", "content-type"))
                return self.parent.open(compat_urllib_request.Request(req.get_full_url(),
                                                 headers=newheaders,
                                                 origin_req_host=req.get_origin_req_host(),
                                                 unverifiable=True))

        # Build our opener
        opener = compat_urllib_request.OpenerDirector()
        for handler in [compat_urllib_request.HTTPHandler, compat_urllib_request.HTTPDefaultErrorHandler,
                        HTTPMethodFallback, HEADRedirectHandler,
                        compat_urllib_request.HTTPErrorProcessor, compat_urllib_request.HTTPSHandler]:
            opener.add_handler(handler())

        response = opener.open(HEADRequest(url))
        if response is None:
            raise ExtractorError('Invalid URL protocol')
        return response

    def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        entries = [{
            '_type': 'url',
            'url': e.find('link').text,
            'title': e.find('title').text,
        } for e in doc.findall('./channel/item')]

        return {
            '_type': 'playlist',
            'id': url,
            'title': playlist_title,
            'description': playlist_desc,
            'entries': entries,
        }

    def _real_extract(self, url):
        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            default_search = self._downloader.params.get('default_search')
            if default_search is None:
                default_search = 'auto'

            if default_search == 'auto':
                if '/' in url:
                    self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
                    return self.url_result('http://' + url)
                else:
                    return self.url_result('ytsearch:' + url)
            else:
                assert ':' in default_search
                return self.url_result(default_search + url)
        video_id = os.path.splitext(url.split('/')[-1])[0]

        self.to_screen('%s: Requesting header' % video_id)

        try:
            response = self._send_head(url)

            # Check for redirect
            new_url = response.geturl()
            if url != new_url:
                self.report_following_redirect(new_url)
                return self.url_result(new_url)

            # Check for direct link to a video
            content_type = response.headers.get('Content-Type', '')
            m = re.match(r'^(?P<type>audio|video|application(?=/ogg$))/(?P<format_id>.+)$', content_type)
            if m:
                upload_date = response.headers.get('Last-Modified')
                if upload_date:
                    upload_date = unified_strdate(upload_date)
                return {
                    'id': video_id,
                    'title': os.path.splitext(url_basename(url))[0],
                    'formats': [{
                        'format_id': m.group('format_id'),
                        'url': url,
                        'vcodec': 'none' if m.group('type') == 'audio' else None
                    }],
                    'upload_date': upload_date,
                }

        except compat_urllib_error.HTTPError:
            # This may be a stupid server that doesn't like HEAD, our UA, or so
            pass

        try:
            webpage = self._download_webpage(url, video_id)
        except ValueError:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            raise ExtractorError('Failed to download URL: %s' % url)

        self.report_extraction(video_id)

        # Is it an RSS feed?
        try:
            doc = xml.etree.ElementTree.fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return self._extract_rss(url, video_id, doc)
        except compat_xml_parse_error:
            pass

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')

        # video uploader is domain name
        video_uploader = self._search_regex(
            r'^(?:https?://)?([^/]*)/.*', url, 'video uploader')

        # Look for BrightCove:
        bc_urls = BrightcoveIE._extract_brightcove_urls(webpage)
        if bc_urls:
            self.to_screen('Brightcove video detected.')
            entries = [{
                '_type': 'url',
                'url': smuggle_url(bc_url, {'Referer': url}),
                'ie_key': 'Brightcove'
            } for bc_url in bc_urls]

            return {
                '_type': 'playlist',
                'title': video_title,
                'id': video_id,
                'entries': entries,
            }

        # Look for embedded (iframe) Vimeo player
        mobj = re.search(
            r'<iframe[^>]+?src="((?:https?:)?//player\.vimeo\.com/video/.+?)"', webpage)
        if mobj:
            player_url = unescapeHTML(mobj.group(1))
            surl = smuggle_url(player_url, {'Referer': url})
            return self.url_result(surl, 'Vimeo')

        # Look for embedded (swf embed) Vimeo player
        mobj = re.search(
            r'<embed[^>]+?src="(https?://(?:www\.)?vimeo\.com/moogaloop\.swf.+?)"', webpage)
        if mobj:
            return self.url_result(mobj.group(1), 'Vimeo')

        # Look for embedded YouTube player
        matches = re.findall(r'''(?x)
            (?:<iframe[^>]+?src=|embedSWF\(\s*)
            (["\'])(?P<url>(?:https?:)?//(?:www\.)?youtube\.com/
                (?:embed|v)/.+?)
            \1''', webpage)
        if matches:
            urlrs = [self.url_result(unescapeHTML(tuppl[1]), 'Youtube')
                     for tuppl in matches]
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for embedded Dailymotion player
        matches = re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?dailymotion\.com/embed/video/.+?)\1', webpage)
        if matches:
            urlrs = [self.url_result(unescapeHTML(tuppl[1]), 'Dailymotion')
                     for tuppl in matches]
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for embedded Wistia player
        match = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:fast\.)?wistia\.net/embed/iframe/.+?)\1', webpage)
        if match:
            return {
                '_type': 'url_transparent',
                'url': unescapeHTML(match.group('url')),
                'ie_key': 'Wistia',
                'uploader': video_uploader,
                'title': video_title,
                'id': video_id,
            }

        # Look for embedded blip.tv player
        mobj = re.search(r'<meta\s[^>]*https?://api\.blip\.tv/\w+/redirect/\w+/(\d+)', webpage)
        if mobj:
            return self.url_result('http://blip.tv/a/a-'+mobj.group(1), 'BlipTV')
        mobj = re.search(r'<(?:iframe|embed|object)\s[^>]*(https?://(?:\w+\.)?blip\.tv/(?:play/|api\.swf#)[a-zA-Z0-9]+)', webpage)
        if mobj:
            return self.url_result(mobj.group(1), 'BlipTV')

        # Look for Bandcamp pages with custom domain
        mobj = re.search(r'<meta property="og:url"[^>]*?content="(.*?bandcamp\.com.*?)"', webpage)
        if mobj is not None:
            burl = unescapeHTML(mobj.group(1))
            # Don't set the extractor because it can be a track url or an album
            return self.url_result(burl)

        # Look for embedded Vevo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:cache\.)?vevo\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Ooyala videos
        mobj = re.search(r'player.ooyala.com/[^"?]+\?[^"]*?(?:embedCode|ec)=([^"&]+)', webpage)
        if mobj is not None:
            return OoyalaIE._build_url_result(mobj.group(1))

        # Look for Aparat videos
        mobj = re.search(r'<iframe src="(http://www\.aparat\.com/video/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Aparat')

        # Look for MPORA videos
        mobj = re.search(r'<iframe .*?src="(http://mpora\.(?:com|de)/videos/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Mpora')

        # Look for embedded Novamov player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>http://(?:(?:embed|www)\.)?novamov\.com/embed\.php.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Novamov')

        # Look for embedded Facebook player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https://www\.facebook\.com/video/embed.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Facebook')

        # Look for embedded Huffington Post player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://embed\.live\.huffingtonpost\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'HuffPost')

        # Start with something easy: JW Player in SWFObject
        mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Look for gorilla-vid style embedding
            mobj = re.search(r'(?s)(?:jw_plugins|JWPlayerOptions).*?file\s*:\s*["\'](.*?)["\']', webpage)
        if mobj is None:
            # Broaden the search a little bit
            mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit: JWPlayer JS loader
            mobj = re.search(r'[^A-Za-z0-9]?file["\']?:\s*["\'](http(?![^\'"]+\.[0-9]+[\'"])[^\'"]+)["\']', webpage)
        if mobj is None:
            # Try to find twitter cards info
            mobj = re.search(r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage)
        if mobj is None:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them (eg.: statigr.am)
            m_video_type = re.search(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                mobj = re.search(r'<meta.*?property="og:video".*?content="(.*?)"', webpage)
        if mobj is None:
            # HTML5 video
            mobj = re.search(r'<video[^<]*(?:>.*?<source.*?)? src="([^"]+)"', webpage, flags=re.DOTALL)
        if mobj is None:
            raise ExtractorError('Unsupported URL: %s' % url)

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            raise ExtractorError('Did not find a valid video URL at %s' % url)

        video_url = mobj.group(1)
        video_url = compat_urlparse.urljoin(url, video_url)
        video_id = compat_urllib_parse.unquote(os.path.basename(video_url))

        # Sometimes, jwplayer extraction will result in a YouTube URL
        if YoutubeIE.suitable(video_url):
            return self.url_result(video_url, 'Youtube')

        # here's a fun little line of code for you:
        video_id = os.path.splitext(video_id)[0]

        return {
            'id': video_id,
            'url': video_url,
            'uploader': video_uploader,
            'title': video_title,
        }
