#!/usr/bin/env python
# coding: utf-8

# In[3]:


# Web Scraper for the website "Sports Reference: College Basketball" & "Pomeroy College Basketball Ratings"
# for NCAA Tournament seed, round, and adjusted efficiency margin data from 2002-2021

import numpy as np
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

# Create empty DataFrames to store the data created in the for loop
seeddata = pd.DataFrame()
kp_data = pd.DataFrame()

# Specify the years of tournament data, 
# 2020 was omitted due to the cancellation of the tournament (COVID-19),
# 2002 was the first year adjusted efficiency data is available
years = [*range(2002,2022)]
years.remove(2020)

# Create a for loop to create the url's for each year's Pomeroy data, 
# then open the url and save the html code, 
# then convert the html code to data readable by Python using Beautiful Soup
for year in years:
    year_kp_url = "https://kenpom.com/index.php?y={}".format(year)
    year_kp_html = urlopen(year_kp_url)
    year_kp_soup = BeautifulSoup(year_kp_html)
    year_kp_soup.find_all("span", {'seed-nit'})
    
    # Remove the seed number from teams in the NIT,
    # which will make it easier to filter these teams out later
    for span in year_kp_soup.find_all("span", class_='seed-nit'):
        span.decompose()
    
    # Get the text for the headers and row data,
    kp_headers = [th.getText() for th in year_kp_soup.findAll('tr')[1].findAll('th')]
    kp_rows = year_kp_soup.findAll('tr',class_ = lambda table_rows: table_rows != "thead")
    kp_team_stats = [[td.getText() for td in kp_rows[i].findAll(['td','th'],class_ = lambda td: td != 'td-right')] for i in range(len(kp_rows))]

    # Remove 1st 2 headers from row data
    kp_team_stats = kp_team_stats[2:]

    # Create a Pandas DataFrame from the efficiency data retrieved
    kp_yeardata = pd.DataFrame(kp_team_stats, columns = kp_headers)

    # Filter out all teams who do not have a seed number next to their name
    # i.e. teams who did not make the NCAA tournament
    kp_yeardata = kp_yeardata[kp_yeardata['Team'].str.endswith(('1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16'))]
    
    # Remove the seed number from each team's name,
    # then delete leading and ending spaces
    kp_yeardata['Team'] = kp_yeardata['Team'].str.replace('[(\d+)]','')
    kp_yeardata['Team'] = kp_yeardata['Team'].str.strip()
    
    # Create a dictionary of which teams each year 'made' the NCAA tournmant
    # (made the play-in games), but did not win and therefore did not advance to the Round of 64
    playin_dict = {2021:["Mount St. Mary's",'Michigan St.','Appalachian St.','Wichita St.'],2019:['North Carolina Central','Temple','Prairie View A&M',"St. John's"],
                  2018:['LIU Brooklyn','UCLA','Arizona St.','North Carolina Central'],2017:['New Orleans','Providence','North Carolina Central','Wake Forest'],
                  2016:['Fairleigh Dickinson','Tulsa','Vanderbilt','Southern'],2015:['Boise St.','Manhattan','North Florida','BYU'],
                  2014:['Iowa','Texas Southern','Xavier',"Mount St. Mary's"],2013:['LIU Brooklyn','Liberty','Middle Tennessee','Boise St.'],
                  2012:['California','Lamar','Mississippi Valley St.','Iona'],2011:['UAB','Alabama St.','Arkansas Little Rock','USC'],
                  2010:['Winthrop'],2009:['Alabama St.'],2008:['Coppin St.'],
                  2007:['Florida A&M'],2006:['Hampton'],
                  2005:['Alabama A&M'],2004:['Lehigh'],
                  2003:['Texas Southern'],2002:['Alcorn St.']}
    kp_yeardata = kp_yeardata[~kp_yeardata['Team'].isin(playin_dict[year])]

    # Delete all unncessecary columns,
    # and specify the correct adjusted efficiency margin column
    kp_yeardata = kp_yeardata[['Team','AdjEM']]
    kp_yeardata.columns = ['Team','E.M.','O','D']
    kp_yeardata.drop(['O','D'], axis=1, inplace=True)

    # Fill empty rows with NaN, then delete these rows
    kp_yeardata.replace('', np.nan, inplace=True)
    kp_yeardata.dropna(inplace=True)

    # Delete rows with extra header data (labeled as 'Team')
    kp_yeardata = kp_yeardata[kp_yeardata.Team != 'Team']

    # Change adjusted efficiency margin number from string to float
    kp_yeardata['E.M.'] = kp_yeardata['E.M.'].astype(float)

    # Specify the year of each team's Pomeroy data
    kp_yeardata['Year'] = year

    # Create a DataFrame of the full data by appending all the dataframes created in the for loop
    kp_data = kp_data.append(kp_yeardata)

    # Open the url and save the html code, 
    # then convert the html code to data readable by Python using Beautiful Soup
    year_url = "https://www.sports-reference.com/cbb/postseason/{}-ncaa.html".format(year)
    year_html = urlopen(year_url)
    year_soup = BeautifulSoup(year_html)

    # Specify each possible region of the tournament as they are named on the website,
    # specifying all possible region names is necessary since some year's use different region names
    regions = ['east', 'west', 'midwest', 'south', 'southeast', 'southwest','minneapolis','atlanta',
              'oakland','washington','syracuse','albuquerque','austin','chicago','stlouis',
              'eastrutherford','phoenix']

    # Create a for loop to extract the <div> section for each seperate region
    for region in regions:
        tourney_region = year_soup.select_one("div#{}".format(region))

        # Filter results to only use regions containing data,
        # this is neccesary to exclude NoneType's created when searching through all possible region names
        if tourney_region != None:      

            # Create a while loop to only take the first 16 iterations of teams in each region, 
            # this is neccessary to only select data from 1st round teams (16 teams) 
            t = 0
            while t <= 16:
                tourney_team = tourney_region.select_one("div.round")
                t = t + 1
            else:
                
                playin = tourney_region.select_one('p')
                
                # Create a for loop to extract the url's for each team's individual gamelog page, 
                # then open the url and save the html code, 
                # then convert the html code to data readable by Python using Beautiful Soup
                for link in tourney_team.find_all('a'):
                    links = link.get('href') 
                    if links.startswith('/cbb/s') == True:
                        team_url = 'https://www.sports-reference.com' + links
                        team_html = urlopen(team_url)
                        team_soup = BeautifulSoup(team_html)

                        # Create a dictionary to store scraped data
                        yeardict = {}

                        # Store year number in the dictionary
                        yeardict[year] = {}  

                        # Store team name in the dictionary
                        part_url = re.sub('https://www.sports-reference.com/cbb/schools/','',team_url)
                        yeardict[year][re.sub('/(\d+).html','',part_url).title()] = {}

                        # Create an elif statement to determine which round each team made it to in the tournament,
                        # then store the round number in the dictionary
                        homepage = team_soup.select_one('div#info')
                        homepage_text= [hp.getText()for hp in homepage.findAll('p')]
                        if any('Won National Final' in text for text in homepage_text):
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 7
                        elif any('Lost National Final' in text for text in homepage_text):
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 6 
                        elif any('National Semifinal' in text for text in homepage_text):
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 5
                        elif any('Regional Final' in text for text in homepage_text):
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 4
                        elif any('Regional Semifinal' in text for text in homepage_text):
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 3

                        # 2015-2011 tournaments use 2nd round as 1st & 3rd as 2nd, 
                        # play-in games labeled as 1st round when in fact they are not part of the actual tournament
                        elif year in range(2011,2016):
                            if any('Third Round' in text for text in homepage_text):
                                yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 2
                            else:
                                yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 1

                        # This is corrected from the 2016 tournament onward, and before 2011
                        else:
                            if any('Second Round' in text for text in homepage_text):
                                yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 2
                            else:
                                yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Round'] = 1

                        # Create an if/else statement to to determine each team's seed in the tournament,
                        # then store the seed number in the dictionary
                        homepage_text= homepage_text[-1]
                        seeds = re.search('(\d+) seed', homepage_text)
                        if seeds is not None:
                            yeardict[year][re.sub('/(\d+).html','',part_url).title()]['Seed'] = seeds.group(0).replace(' seed','')
                            
                            # Create a DataFrame from the dictonary data
                            yeardata = pd.DataFrame.from_dict({(i,j): yeardict[i][j] 
                                                    for i in yeardict.keys() 
                                                    for j in yeardict[i].keys()},
                                                   orient='index')
                            
                            # Find each team's opponent's name in each round,
                            # then save each opponent's name in a seperate column in the DataFrame
                            homepage_text = re.sub('.+Opening.+','',homepage_text)
                            homepage_text = re.sub('.+First Four.+','',homepage_text)
                            if year in range(2011,2016):
                                homepage_text = re.sub('.+First Round.+','',homepage_text)
                            homepage_text = re.sub('.+[a-z]\)','',homepage_text)
                            oppname = re.findall('#\d+.+',homepage_text)
                            for num, team in enumerate(oppname):
                                name = re.sub('#\d+','',team)
                                name = name.strip()
                                yeardata['Opp_' + str(num+1)] = name
                            
                            # Find each team's opponent's seed in each round,
                            # then save each opponent's name in a seperate column in the DataFrame
                            oppseed = re.findall('[$#]\d+',homepage_text)
                            oppseed = [re.sub('#','',seed) for seed in oppseed]
                            oppseed = [int(seed) for seed in oppseed]
                            yeardata.reset_index(inplace=True)
                            yeardata['Seed'] = [int(seed) for seed in yeardata['Seed']]
                            
                            # Compare each team's seed with their last opponent's seed (the game they lost),
                            # to determine if the team lost in an upset or not
                            if yeardata.at[0,'Seed'] < oppseed[-1]:
                                yeardata['Final Round Outcome'] = 'Upset'
                            else:
                                yeardata['Final Round Outcome'] = 'No Upset'
                            
                            # Create a DataFrame of the full data by appending all the dataframes created in the for loop
                            seeddata = seeddata.append(yeardata)
                            
# Reset the index of the DataFrame in order to correctly name the columns
seeddata.columns = ['Year1','Team1','Round','Seed','Opp_1','Opp_2','Opp_3','Opp_4','Opp_5','Opp_6','Final Rd']

# Rename various teams in the seeddata DataFrame to mirror that of the kp_data DataFrame
teamnames_dict = {1:{'old':'California-Santa-Barbara','new':'UC Santa Barbara'},2:{'old':'Brigham-Young','new':'BYU'},
                 3:{'old':'Louisiana-State','new':'LSU'},4:{'old':'Virginia-Commonwealth','new':'VCU'},
                 5:{'old':'Ucla','new':'UCLA'},6:{'old':'North-Carolina-Greensboro','new':'UNC Greensboro'},
                 7:{'old':'Southern-California','new':'USC'},8:{'old':'California-Irvine','new':'UC Irvine'},
                 9:{'old':'Central-Florida','new':'UCF'},10:{'old':'Maryland-Baltimore-County','new':'UMBC'},
                 11:{'old':'North-Carolina-State','new':'N.C. State'},12:{'old':'Texas-Christian','new':'TCU'},
                 13:{'old':'California-Davis','new':'UC Davis'},14:{'old':'North-Carolina-Asheville','new':'UNC Asheville'},
                 15:{'old':'North-Carolina-Wilmington','new':'UNC Wilmington'},16:{'old':'Southern-Methodist','new':'SMU'},
                 17:{'old':'Alabama-Birmingham','new':'UAB'},18:{'old':'Nevada-Las-Vegas','new':'UNLV'},
                 19:{'old':'Long-Island-University','new':'LIU Brooklyn'},20:{'old':'Texas-San-Antonio','new':'UTSA'},
                 21:{'old':'Texas-El-Paso','new':'UTEP'},22:{'old':'Texas-Arlington','new':'UT Arlington'},
                 23:{'old':'Iupui','new':'IUPUI'},24:{'old':'Pennsylvania','new':'Penn'},25:{'old':'Depaul','new':'DePaul'},
                  26:{'old':'Penn State','new':'Penn St.'},27:{'old':'Delaware State','new':'Delaware St.'}
                 }

for num in range(1,28):
    seeddata['Team1'] = seeddata['Team1'].str.replace(teamnames_dict[num]['old'],teamnames_dict[num]['new'])

oppnames_dict = {1:{'old':'California Santa-Barbara','new':'UC Santa Barbara'},2:{'old':'Brigham Young','new':'BYU'},
                 3:{'old':'Louisiana State','new':'LSU'},4:{'old':'Virginia Commonwealth','new':'VCU'},
                 5:{'old':'Ucla','new':'UCLA'},6:{'old':'North Carolina-Greensboro','new':'UNC Greensboro'},
                 7:{'old':'Southern California','new':'USC'},8:{'old':'California Irvine','new':'UC Irvine'},
                 9:{'old':'Central Florida','new':'UCF'},10:{'old':'Maryland-Baltimore County','new':'UMBC'},
                 11:{'old':'North Carolina State','new':'N.C. State'},12:{'old':'Texas Christian','new':'TCU'},
                 13:{'old':'California Davis','new':'UC Davis'},14:{'old':'North Carolina-Asheville','new':'UNC Asheville'},
                 15:{'old':'North Carolina-Wilmington','new':'UNC Wilmington'},16:{'old':'Southern Methodist','new':'SMU'},
                 17:{'old':'Alabama-Birmingham','new':'UAB'},18:{'old':'Nevada-Las Vegas','new':'UNLV'},
                 19:{'old':'Long Island University','new':'LIU Brooklyn'},20:{'old':'Texas San-Antonio','new':'UTSA'},
                 21:{'old':'Texas El-Paso','new':'UTEP'},22:{'old':'Texas Arlington','new':'UT Arlington'},
                 23:{'old':'Iupui','new':'IUPUI'},24:{'old':'Pennsylvania','new':'Penn'},25:{'old':'Depaul','new':'DePaul'},
                  26:{'old':'Penn State','new':'Penn St.'},27:{'old':'Delaware State','new':'Delaware St.'},
                  28:{'old':'University of California','new':'California'},
                 29:{'old':'Little Rock','new':'Arkansas Little Rock'}
                 }

for num in range(1,30):   
    seeddata['Opp_1'] = seeddata['Opp_1'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
    seeddata['Opp_2'] = seeddata['Opp_2'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
    seeddata['Opp_3'] = seeddata['Opp_3'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
    seeddata['Opp_4'] = seeddata['Opp_4'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
    seeddata['Opp_5'] = seeddata['Opp_5'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
    seeddata['Opp_6'] = seeddata['Opp_6'].str.replace(oppnames_dict[num]['old'],oppnames_dict[num]['new'])
kp_data['Team'] = kp_data['Team'].str.replace('Troy St.','Troy')

# Sort each DataFrame alpabetically by Team name
# The previous step was necessary so the order of teams would be the same in each DataFrame
kp_data.sort_values(by=['Team','Year'],inplace=True)
seeddata.sort_values(by=['Team1','Year1'],inplace=True)

# Reset each DataFrame's index 
kp_data.reset_index(drop=True, inplace=True)
seeddata.reset_index(drop=True, inplace=True)

# Merge seeddata & kp_data DataFrames, then delete duplicate columns
# The previous steps were necessary so each DataFrame would be ordered the same to merge,
# merge() could not be used since team names were not identical between DataFrames
fulldata = pd.concat([seeddata, kp_data],axis=1)
fulldata.drop(columns=['Year1','Team1'],inplace=True)

# Export fulldata DataFrame as .csv file  
fulldata.to_csv('/Users/joshtkraus/Documents/Data Analysis/fulldata.csv')


# In[ ]:




