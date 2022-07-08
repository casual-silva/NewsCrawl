#!/home/tlrobot/anaconda3/envs/news_crawl/bin/python
# -*- coding: utf-8 -*-
import re
import sys
from scrapyd_client.deploy import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
