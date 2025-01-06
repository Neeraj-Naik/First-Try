import pandas as pd
import re
from pathlib import Path

HomeDir = Path.cwd()
TeamDataFile = HomeDir / 'TeamData.csv'
PotDataFile = HomeDir / 'PotData.csv'

if TeamDataFile.exists() and PotDataFile.exists():
    print('File requirements already satisfied.')

else:
    print('Creating Files ......')

    OQ_countries = ['Austria','Belarus','Denmark','France','Germany','Norway','Poland']         # Olympic Qualified Countries

    data = pd.read_html('https://en.wikipedia.org/wiki/2016%E2%80%9317_Champions_Hockey_League')[1]
    cols = data.columns
    data = pd.read_html('https://en.wikipedia.org/wiki/2016%E2%80%9317_Champions_Hockey_League',extract_links='all')[1]
    data.columns = cols

    team_data = {
        'Team' : [],
        'Country' : [],
        'League' : [],
        'Olympic Qualified' : []
    }

    for indx in range(data.shape[0]):
        entry = data.loc[indx,'Team']
        team_data['Team'].append(entry[0])
        cntry = entry[1].split('/')[2]
        if cntry in OQ_countries:
            team_data['Olympic Qualified'].append('True')
        else:
            team_data['Olympic Qualified'].append('False')
        team_data['Country'].append(entry[1].split('/')[2])
        team_data['League'].append(data.loc[indx,'League'][0])

    team_data = pd.DataFrame(team_data)

    print('TeamData.csv created')
    team_data.to_csv('TeamData.csv',index=False)                                                            # writing team data 

    data = pd.read_html('https://en.wikipedia.org/wiki/2016%E2%80%9317_Champions_Hockey_League')[2]         # pot data

    pot_data = {}

    for pot in data.columns:
        pot_data.update({pot:[]})
        strng = data.loc[0,pot]
        while bool(re.search('\S',strng)):
            # print(strng)
            for team in team_data['Team']:
                match_team = re.search(team,strng)
                if bool(match_team):
                    pot_data[pot].append(team)
                    cut = match_team.span()
                    strng = strng[:cut[0]] + strng[cut[1]:]
                    # print(strng)
                    break

    pot_data = pd.DataFrame(pot_data)

    print('PotData.csv created')
    pot_data.to_csv('PotData.csv',index=False)                                                               # writing pot data