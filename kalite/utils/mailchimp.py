import requests
import settings

def mailchimp_subscribe(email, mc_url=settings.CENTRAL_SUBSCRIBE_URL):
    """Do the post request to mailchimp, return the MailChimp HTML result"""
    r = requests.post(mc_url, data={'EMAIL' : email})
    return r.text

