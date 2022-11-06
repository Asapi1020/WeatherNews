import PySimpleGUI as sg
import requests
import os
from bs4 import BeautifulSoup

Link_Somewhere = "https://weathernews.jp/onebox/tenki/Prefecture/xxxxx/" # You should replace here with a certain link
Title = ""
wInfo_day2 = []
wInfo_Time = []
wInfo_Week = []
DL_log = []
temp_f = []
sg.theme("DefaultNoMoreNagging")

def DownloadFile(url_img):
    if url_img in DL_log:
        return

    DL_log.append(url_img)
    res_img = requests.get(url_img)
    name_img = 'WN_' + os.path.basename(url_img)
    with open(name_img, 'wb') as f:
        f.write(res_img.content)
        temp_f.append(name_img)

def DeleteFiles():
    for f in temp_f:
        os.remove(f)

def GetDay2Info(BaseSoup):
    Info = [[""]*6 for i in range(2)]
    soup_temp = BaseSoup.find("section", class_="wTable day2")
    soup_list = soup_temp.find_all("div", class_="wTable__group")

    for i, s in enumerate(soup_list):
        Info[i][0] = s.find("div", class_="wTable__day").p.string
        Info[i][1] = s.find("img", class_="wIcon")['src']
        DownloadFile("https:" + Info[i][1])
        Info[i][2] = s.find("p", class_="temp__h").find("span", class_="text").get_text()
        Info[i][3] = s.find("p", class_="temp__l").find("span", class_="text").get_text()
        RainPoss = s.find_all("div", class_="day2__temp")[1].find_all("span", class_="text")
        Info[i][4] = RainPoss[0].get_text()
        Info[i][5] = RainPoss[1].get_text()

    return Info

def GetTimeInfo(BaseSoup):
    Info = []
    soup_temp = BaseSoup.find("section", class_="wTable time")
    soup_list = soup_temp.find_all("div", class_="wTable__group")

    for s in soup_list:
        InfoG = []
        InfoG.append(s.find("div", class_="wTable__day").p.string)
        s_time = s.find_all("div", class_="wTable__row")
        
        for st in s_time:
            InfoR = []
            InfoR.append(st.find("p", class_="time").get_text())
            url_img = st.find("img", class_="wIcon")["src"]
            InfoR.append(url_img)
            DownloadFile("https:" + url_img)
            InfoR.append(st.find("p", class_="r").get_text())
            InfoR.append(st.find("p", class_="t").get_text())
            InfoG.append(InfoR)
            
        Info.append(InfoG)

    return Info

def GetWeekInfo(BaseSoup):
    Info = []
    soup_temp = BaseSoup.find("section", class_="wTable week")
    soup_temp = soup_temp.find("div", class_="wTable__content")
    soup_list = soup_temp.find_all("div", class_="wTable__row")

    for s in soup_list:
        InfoR = []
        InfoR.append(s.find("p", class_="day").get_text())
        url_img = s.find("img", class_="wIcon")["src"]
        InfoR.append(url_img)
        DownloadFile("https:" + url_img)
        InfoR.append(s.find("p", class_="h").get_text())
        InfoR.append(s.find("p", class_="l").get_text())
        InfoR.append(s.find("p", class_="r").get_text())
        Info.append(InfoR)

    return Info

res = requests.get(Link_Somewhere)
soup = BeautifulSoup(res.text, "html.parser")

def SetupDay2Info():
    wInfo_day2 = GetDay2Info(soup)
    table_v = ["日", "天気", "気温", "降水確率"]
    row = []
    row.append(sg.Column([ [sg.Text(elem)] for elem in table_v ]))

    for idx, Info in enumerate(wInfo_day2):
        InfoR = [sg.T("今日")] if idx==0 else [sg.T("明日")]
        InfoR.append(sg.T(Info[0]))
        InfoR.append(sg.Image("WN_" + os.path.basename(Info[1])))
        i = 2
        while i < 6:
            table_v = ["最高", "最低"] if i==2 else ["午前", "午後"]
            InfoR.append(sg.Column([[sg.T(table_v[0]),
                                     sg.T(Info[i]),
                                     sg.T(table_v[1]),
                                     sg.T(Info[i+1])]]))
            i+=2
        row.append(sg.Column([ [InfoR[i]] for i in range(5) ]))
    return [sg.Pane([r], pad=((0,0),(0,0))) for r in row]

def SetupTimeInfo():
    wInfo_Time = GetTimeInfo(soup)
    table = []

    for Info in wInfo_Time:
        temp = []
        h = ["時", "天気", "降水", "気温"]
        temp.append(sg.Pane([sg.Column([[sg.T(elem)] for elem in h])]))
        i = 1
        while i < len(Info):
            h = []
            h.append(sg.T(Info[i][0]))
            h.append(sg.Image('WN_' + os.path.basename("https:"+Info[i][1]), subsample=4))
            h.append(sg.T(Info[i][2]))
            h.append(sg.T(Info[i][3]))
            temp.append(sg.Pane([sg.Column([[elem] for elem in h])], pad=((0,0),(0,0))))
            i += 1

        table.append(sg.Tab(Info[0], [[sg.Column([temp])]]))

    return [sg.TabGroup([table])]

def SetupWeekInfo():
    wInfo_Week = GetWeekInfo(soup)
    table = []
    h = ["日", "天気", "最高", "最低", "降水"]
    table.append(sg.Pane([sg.Column([[sg.T(elem)] for elem in h])]))

    for Info in wInfo_Week:
        h = []
        h.append(sg.T(Info[0]))
        h.append(sg.Image('WN_' + os.path.basename("https:"+Info[1]), subsample=4))
        h.append(sg.T(Info[2]))
        h.append(sg.T(Info[3]))
        h.append(sg.T(Info[4]))
        table.append(sg.Pane([sg.Column([[elem] for elem in h])], pad=((0,0),(0,0))))

    return table

def SetupWindow():
    Title = soup.find("h1", class_="index__tit").string
    layout = [ [sg.Button(key="refresh", image_filename="Refresh.png"), sg.T(Title)] ,
               SetupDay2Info(),
               [sg.T("")],
               [sg.Frame("1時間ごと",[SetupTimeInfo()])],
               [sg.T("")],
               [sg.Frame("10日間",[SetupWeekInfo()])]
               ]
    return sg.Window("Weather News", layout, resizable=True, size=(1350, 800))

window = SetupWindow()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == "refresh":
        window.close()
        window = SetupWindow()

window.close()
DeleteFiles()
