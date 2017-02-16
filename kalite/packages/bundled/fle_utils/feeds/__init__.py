from django.contrib.syndication.views import Feed
from models import FeedListing
from django.utils.feedgenerator import Atom1Feed

class RssSiteNewsFeed(Feed):

    link = "/feeds/rss/"

    def items(self):
        return FeedListing.objects.order_by('-posted_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description
        
    def item_link(self, item):
        return item.url
        

class AtomSiteNewsFeed(RssSiteNewsFeed):
    feed_type = Atom1Feed
    item_subtitle = RssSiteNewsFeed.item_description
    
    link = "/feeds/atom/"