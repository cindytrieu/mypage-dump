import requests, re
from fastapi import FastAPI, Form
from bs4 import BeautifulSoup

def get_int(string):
    return int(re.search(r'(\d+)', string).group(1))

class DifficultyStats:
    def __init__(self, score, rate, achieve, play_count):
        self.score = score
        self.rate = rate
        self.achieve = achieve
        self.play_count = play_count

    def __str__(self):
        return self.__dict__
    
    # pink one: total_plays
    # play count: black text about pink oval
    # score: black text next to circle and triangle
    # rate = circle icon (0-13) or none
    # achieve = triangle (0-3)
    #https://wacca.marv-games.jp/web/music/detail 
    
class Song:
    total_plays = 0
    difficulties = []

    def __init__(self, id, name):
        self.id = id
        self.name = name


class User:
    wsid = ""
    response = ""
    songs = []
    headers_form_encoded = {"Content-Type": "application/x-www-form-urlencoded"} 

    def login_request(self):
        print("Logging in with Aime ID {0}...".format(self.id))
        url = "https://wacca.marv-games.jp/web/login/exec"
        self.response = requests.request("POST", url, data = "aimeId={0}".format(self.id), headers=self.headers_form_encoded)
        
    def gen_cookie(self):
        self.wsid = re.search(r'WSID=(\w+);', self.response.headers["Set-Cookie"]).group(1)
        #print("gen_cookie(): new cookie '{0}'".format(self.wsid))
        return "WSID={0}; WUID={0}".format(self.wsid)

    def scrape_song(self, song):
        print("* <{0}> [{1}] ".format(song.id, song.name), end='')

        url = "https://wacca.marv-games.jp/web/music/detail"
        self.response = requests.request("POST", url, data = "musicId={0}".format(song.id), headers=self.headers_form_encoded | { "Cookie": self.gen_cookie() })
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        
        
        song.total_plays = get_int(soup.select_one(".song-info__play-count > span").text)
    

        # Selector for difficulties
        diffs = soup.select(".score-detail__list__song-info")

        song.difficulties = []


        for diff in diffs:
            play_count = get_int(diff.select_one(".song-info__top__play-count").text)
            score = get_int(diff.select_one(".song-info__score").text)
            
            # difficulty name
            # print(diff.select_one(".song-info__top__lv > div").text)

            '''
            {'id': 2070, 'name': 'KALACAKLA', 'total_plays': 8, 'difficulties': [<main.DifficultyStats object at 0x10ad871f0>, <main.DifficultyStats object at 0x10ad87c10>, <main.DifficultyStats object at 0x10ad87370>]}
            {'score': 0, 'rate': 'no_rate', 'achieve': 'no_achieve', 'play_count': 0}
            {'score': 994595, 'rate': 'rate_13', 'achieve': 'achieve3', 'play_count': 1}
            {'score': 983269, 'rate': 'rate_9', 'achieve': 'achieve2', 'play_count': 7}
            '''
            
            # difficulty rate and achieve
            icons = diff.select(".score-detail__icon > div > img")

            temp_rate = icons[0]["src"].replace("/img/web/music/rate_icon/", "").split(".")[0]
            rate = 0

            if temp_rate.startswith("rate_"):
                rate = int(temp_rate.split("_")[1])
                
            temp_achieve = icons[1]["src"].replace("/img/web/music/achieve_icon/", "").split(".")[0]
            achieve = 0

            if temp_achieve.startswith("achieve"):
                achieve = int(temp_achieve.replace("achieve",""))

            diff_stats = DifficultyStats(score, rate, achieve, play_count)
            song.difficulties.append(diff_stats)
         
        print("({0} diffs)".format(len(diffs))) # mark song as done
        #print(song.__dict__)

        #for diff in song.difficulties:
        #    print(diff.__dict__)

    def get_songs(self):
        print("Getting song list...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/music", headers = { "Cookie": self.gen_cookie() })
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        
        # Get song data from song list
        songlist = soup.find_all("form",attrs={"name": re.compile("detail")}, limit=0)
        print("Getting song data for {0} songs...".format(len(songlist)))
        for song in songlist:
            self.songs.append(self.scrape_song(Song(int(song.input["value"]), song.parent.a.div.div.string)))

    def __init__(self, id):
        self.id = id
        self.login_request()
        self.gen_cookie()
        self.get_songs()
        


app = FastAPI()

@app.post("/")
async def root(aimeId: str = Form()):
    user = User(aimeId)

    return "Success"