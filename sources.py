from classes import Source

##RSS Sources

#Media

#New York Times Economy feed (includes much of Upshot)
NYT = Source(name = "New York Times", rss = "http://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
	source_type = "RSS", link_tag = "link")

#Atlantic business feed
Atlantic = Source(name = "The Atlantic", rss = "http://feeds.feedburner.com/AtlanticBusinessChannel",
	source_type = "RSS", link_tag = "link")

#Fivethirtyeight economics features feed
FiveThirtyEight = Source(name = "FiveThirtyEight", rss = "http://fivethirtyeight.com/economics/feed/",
	source_type = "RSS", link_tag = "link")

#Economist economics feed
Economist = Source(name = "The Economist", rss = "http://www.economist.com/sections/economics/rss.xml",
	source_type = "RSS", link_tag = "link")

#The Conversation, economics and business feed
Conversation = Source(name = "The Conversation", rss = "http://theconversation.com/us/business/articles.atom",
	source_type = "RSS", link_tag = "link")

#RealClearMarkets, a financial op-ed aggregator
RealClearMarkets = Source(name = "RealClearMarkets", rss = "http://www.realclearmarkets.com/index.xml",
	source_type = "RSS", link_tag = "originallink")

#Think tanks

#Economic Policy Institute (labor-oriented think tank)
EPI = Source(name = "Economic Policy Institute", rss = "http://www.epi.org/blog/feed/",
			source_type = "RSS", link_tag = "link")

Brookings = Source(name = "Brookings", rss = "http://webfeeds.brookings.edu/brookingsrss/topics/economics?format=xml",
	source_type = "RSS", link_tag = "link", 
	exclude_words = "hutchins roundup:event:webcast:brookings today:weekend reads:africa in the news")

CFR = Source(name = "Council on Foreign Relations", rss = "http://feeds.cfr.org/issue/economics",
	source_type = "RSS", link_tag = "link", 
	exclude_words = "event:must reads:the world next week:watch this meeting:media call")

Peterson = Source(name = "Peterson Institute", rss = "http://feeds.feedburner.com/peterson-update", 
	source_type = "RSS", link_tag = "link",
	exclude_words = "event:news release:peterson institute")

global global_rss_sources 

global_rss_sources = [EPI, NYT, Atlantic, FiveThirtyEight, Economist, Conversation, 
	Brookings, CFR, Peterson, RealClearMarkets]


##Blog aggregator sources

Thoma = Source(name = "Thoma", rss = "http://feeds.feedburner.com/EconomistsView", 
	source_type = "aggregator", include_words = "Links for")

MarginalRevolution = Source(name = "Marginal Revolution", rss = "http://feeds.feedburner.com/marginalrevolution/feed",
	source_type = "aggregator", include_words = "ssorted links", 
	exclude_words = "http://marginalrevolution.com")

EquitableGrowth = Source(name = "Equitable Growth", rss = "http://equitablegrowth.org/feed/",
	source_type = "aggregator", include_words = "Must-Reads", exclude_words = 'http://equitablegrowth.org')

global global_aggregators

global_aggregators = [Thoma, MarginalRevolution, EquitableGrowth]

#Need better filters to do econ only: Vox, Quartz, Project Syndicate, Wonkblog
#RSS currently not working: New Yorker