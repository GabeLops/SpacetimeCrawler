import logging #for printing on console     
import csv     #for creating csv files and reading  
import tldextract as extractor  
from datamodel.search.Glops_datamodel import GlopsLink, OneGlopsUnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree #parsing xml files
from collections import Counter
import re, os 
from time import time
from uuid import uuid4 #creates unique identifiers

from urlparse import urlparse, parse_qs 

#
logger = logging.getLogger(__name__) 
LOG_HEADER = "[CRAWLER]" 
subdomain_count = [] #holds all subdomains
page_max_link = ''
pages = 0

@Producer(GlopsLink)
@GetterSetter(OneGlopsUnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "Glops"

    def __init__(self, frame):
        self.app_id = "Glops"
        self.frame = frame


    def initialize(self):
        global subdomain_count
        #self.count = 0
        links = self.frame.get_new(OneGlopsUnProcessedLink) #checks if any links are generated
        if len(links) > 0:
            print "Resuming from the previous state."
            with open('analytics.csv', 'rb') as csvfile:
                subdomain_count = list(csv.reader(csvfile))[0]
            self.download_links(links)
        else:
            l = GlopsLink("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneGlopsUnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        global subdomain_count
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            links = extract_next_links(downloaded)
            for l in links:
                if is_valid(l):
                    self.frame.add(GlopsLink(l))
                    subdomain = extractor.extract(l).subdomain
                    subdomain_count.append(subdomain)
                    with open('analytics.csv', 'wb') as csv_file:
                        wr = csv.writer(csv_file, delimiter=',')
                        wr.writerow(list(subdomain_count))


    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")
# Takes html raw data (ie string) and extracts all matched links in the data
# Updates page_max_link to the current url with the highest number of links within it
# Updates the value of pages to the current highest number of links (found in page_max_link)
def extract_next_links(rawDataObj):
    outputLinks = []
    content =  rawDataObj.content
    source = rawDataObj.url
    if rawDataObj.is_redirected == True:
        source = str(rawDataObj.final_url)
    if content != '':
        #htmlElem = html.document_fromstring(content) 
        content = html.make_links_absolute(content, source) #converts relative url to absolute url
        matcher = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        matched = re.findall(matcher, content) #absolute urls that matched regex in contents
        matched = [re.sub("'.*", '', url) for url in matched]
        #https://google.com/user
        #/user
        #print(matched)
        outputLinks = matched
    #get page with highest number of urls here
    global pages, page_max_link
    if len(outputLinks) > pages:
        pages = len(outputLinks)
        page_max_link = source
    '''
    rawDataObj is an object of type UrlResponse declared at L20-30
    datamodel/search/server_datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.
    
    Suggested library: lxml
    '''
    return outputLinks

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    parsed = urlparse(url)
    #print('Paresed .....', parsed)
    if parsed.scheme not in set(["http", "https"]):
        return False
    try:
        return "ics.uci" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|admin|checkout|password|favorite|register" \
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        return False

def get_analytics():
    global subdomain_count
    analytics = Counter(subdomain_count) # Count subdomains
    return (dict(analytics), [page_max_link, pages])
    