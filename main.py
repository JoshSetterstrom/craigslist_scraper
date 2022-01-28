import requests, json, yagmail, time, random
from bs4 import BeautifulSoup
from datetime import datetime
from functools import reduce

with open('sites.txt', 'r') as file: urls = file.read().split('\n')
with open('config.txt', 'r') as file: user_config = file.read().split('\n')

start_time = datetime.now()
timeout = user_config[2].split('=')[1].split(', ')


##------------------------------Scheduler------------------------------##

class scheduler():
    def __init__(self):
        self.active   = True

    def schedule(self, start, end, function):
        while True:
            if utils().check_time(start, end):
                if not self.active:
                    print(f"\n\n---------------{time.strftime('%Y-%m-%d %H:%M')}---------------")
                    print(f"Scheduled task is now active and will end at {end} PST.")
                    self.active = True

                function()

            else:
                if self.active:
                    print(f"\n\n---------------{time.strftime('%Y-%m-%d %H:%M')}---------------")
                    print(f"Scheduled task is now inactive and will resume at {start} PST.")
                    self.active = False

                pass

            time.sleep(5)

##---------------------------------------------------------------------##




##--------------------------------Utils--------------------------------##

class utils():
    def __init__(self):
        self.bot_config = json.load(open('data/config.json', 'r'))
        self.user_config = user_config


    def get_pids(self):
        try: return json.load(open('data/pids.json', 'r'))
        except:
            with open('data/pids.json', 'w+') as file: 
                json.dump({'pids': {}}, file, indent=2)
                return {'pids': {}}


    def check_pid(self, element, pids):
        element_pid = element.get('data-pid')

        if not element_pid in pids:
            img_id = (element
                .find("a", {"class": "result-image gallery"})
                .get('data-ids')
                .split(',')[0])[2:]

            return {
                'link': element.find("a", {"class": "result-image gallery"}).get('href'),
                'img': f'https://images.craigslist.org/{img_id}_300x300.jpg',
                'price': element.find('span', {'class': 'result-price'}).text,
                'title': element.find('a', {'data-id': element_pid}).text}


    def create_element(self, result, element):
        result = result + (f"""
            <div style="display:inline-block;min-height:380px;width:250px;border:1px solid #a4dcdb;border-radius:5px;margin:0 10px 10px 0;vertical-align:top;">
            <div style="height:60%;width:100%">
            <img style="display:block;height:175px;margin:0 auto;"src="{element["img"]}">
            </div>
            <div style="height:40%;width:100%;background-color:#f9f9f9;border-radius:0 0 5px 5px">
            <div style="width:100%;height:60%;text-align:center;display:table">
            <span style="display:table-cell;vertical-align:middle;font-size:19px;">{element["title"]}\n{element['price']}</span>
            </div>
            <div style="width:100%;height:40%">
            <a href="{element["link"]}"style="display:table;text-decoration:none;text-align:center;width:60%;height:30px;background-color:#4496df;color:white;margin:15px auto 0 auto;border-radius:3px">
            <span style="display:table-cell;vertical-align:middle;font-size:15px;">New Listing</span>
            </a>
            </div>
            </div>
            </div>""")

        return result


    def send_email(self, elements):
        bot_config = json.load(open('data/config.json', 'r'))

        contents = [(f"""
            <html>
            <body>
            <div style="display:block;max-width:50vw">{elements}</div>
            </body>
            </html>""")]

        yagmail.SMTP(f"{bot_config['bot']['user']}", f"{bot_config['bot']['pass']}").send(
            to=f"{user_config[0].split('=')[1]}",
            subject="New listing on Craigslist",
            contents=contents)


    def uptime(self, start):
        uptime = str(datetime.now() - start).split(':')
        uptime_day = (datetime.now() - start).days

        return (
            f'Uptime: '
            f'{uptime_day} Days '
            f'{uptime[0]} Hours '
            f'{int(uptime[1])} Minutes '
            f'{(uptime[2])[:2]} Seconds')


    def check_time(self, start, end):
        new_time = str(datetime.now().time()).split(':')
        current  = int(new_time[0] + new_time[1])

        if start < end: return True if current > start and current < end else False
        else:           return True if current < start and current > end else False

##---------------------------------------------------------------------##




##---------------------------------Main--------------------------------##

def scraper():
    user_interval = utils().user_config[1].split ('=')[1].split(', ')
    interval = random.randrange(int(user_interval[0]), int(user_interval[1]))

    for i, url in enumerate(urls):
        try:
            print(f"\n\n---------------{time.strftime('%Y-%m-%d %H:%M')}---------------")
            print(utils().uptime(start_time))

            request = requests.get(url)

            if not request: 
                print(f'Site on line {i+1} in sites.txt returned {request.status_code}: {request.reason}')
                continue

            pids     = utils().get_pids() 
            soup     = BeautifulSoup(request.text, 'html.parser')
            items    = soup.find("ul", {"id": "search-results"}).findChildren("li")
            pid_list = list(map(lambda element: element.get('data-pid'), items))

            if not pids.get(url):
                pids[url] = pid_list
                with open('data/pids.json', 'w') as file: json.dump(pids, file, indent=2)
                continue

            elements = list(filter(lambda x: x, map(lambda element: utils().check_pid(element, pids[url]), items)))
            
            if bool(elements):
                print(f"New listing found on Craigslist. Sending email.")
                elements_html = reduce(lambda result, element: utils().create_element(result, element), elements, '')

                utils().send_email(elements_html)

                pids[url] = pid_list

                with open('data/pids.json', 'w') as file:
                    json.dump(pids, file, indent=2)

            else: print('No new listings found.')
        
        except: pass

    print(f'\n\nScraper in interval: {str(interval/60)[:4]} minutes')
    time.sleep(interval)

##---------------------------------------------------------------------##

scheduler().schedule(int(timeout[0]), int(timeout[1]), scraper)