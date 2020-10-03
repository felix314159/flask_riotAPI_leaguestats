from datetime import datetime
from flask import Flask, render_template, request, session
from flask_session import Session
from riotwatcher import LolWatcher, ApiError
from unicodedata import normalize
import flask_app
import json
import pandas as pd


def add_mastery_chest(champion_mastery_list, champion_mastery):
    for index, i in enumerate(champion_mastery):
        if i['chestGranted']:
            champion_mastery_list[index].append("No")
        else:
            champion_mastery_list[index].append("Yes")
    return champion_mastery_list


def add_mastery_levels(champion_mastery_list, champion_mastery):
    for index, i in enumerate(champion_mastery):
        champion_mastery_list[index].insert(1, i['championLevel'])
    return champion_mastery_list


def add_mastery_values(champion_mastery_list, champion_mastery):
    for index, i in enumerate(champion_mastery):
        champion_mastery_list[index].append(i['championPoints'])
    return champion_mastery_list


def champion_id_to_name(championId):
    with open('static/dragontail-10.18.1/10.18.1/data/en_US/champion.json', encoding="utf8") as f:
        data = json.load(f)
    temp = data['data']
    champs = temp.keys()
    for i in champs:
        if int(temp[i]['key']) == championId:
            return temp[i]['id']


def create_live_table(a):
    df = pd.DataFrame(data=a[1:], columns=a[:1])
    df.insert(0, '', ['Champion', 'Spell 1', 'Spell 2', 'Rank', 'Mastery', 'Acc Lvl'])
    dynamic_mastery_table = df.to_html(index=False)
    return dynamic_mastery_table


def create_mastery_table(a):
    df = pd.DataFrame(data=a, columns=['Champion', 'Level', 'Mastery', 'Chest available?'])
    dynamic_mastery_table = df.to_html(index=False)
    session["dynamic_mastery_table"] = dynamic_mastery_table
    return dynamic_mastery_table


def fetch_stats():
    # convert user input to the correct data format
    server_form = request.form.get('server')
    session["server_form"] = server_form

    server = pick_server(session["server_form"])
    session["server"] = server

    summoner_form = request.form['summoner']
    session["summoner_form"] = summoner_form

    summoner = flask_app.watcher.summoner.by_name(session["server"], session["summoner_form"])
    session["summoner"] = summoner

    # make api calls exactly once
    summoner_by_account = flask_app.watcher.summoner.by_account(server, summoner['accountId'])
    session["summoner_by_account"] = summoner_by_account

    try:
        summoner_info = flask_app.watcher.league.by_summoner(server, summoner['id'])[0]
        session["summoner_info"] = summoner_info

        rank = get_rank(summoner_info)
        session["rank"] = rank

        win_loss = get_win_loss(summoner_info)
        session["win_loss"] = win_loss

        session["rank_0"] = rank[0]
        session["rank_1"] = rank[1]
        session["rank_2"] = rank[2]

        temp = rank[1] + " " + rank[2]
        rank_lowercase = rank_to_lowercase([temp], True)
        session["rank_lowercase"] = rank_lowercase

        session["win_loss_0"] = win_loss[0]
        session["win_loss_1"] = win_loss[1]
        session["win_loss_2"] = win_loss[2]
        rounded_wr = round(win_loss[2]*100, 2)
        session["rounded_wr"] = rounded_wr

    except:
        session["summoner_info"] = 0
        session["rank"] = 0
        session["win_loss"] = 0

        session["rank_0"] = "N/A"
        session["rank_1"] = 0
        session["rank_2"] = 0
        session["rank_lowercase"] = 0
        session["win_loss_0"] = 0
        session["win_loss_1"] = 0
        session["win_loss_2"] = 0
        session["rounded_wr"] = 0

    champion_mastery = flask_app.watcher.champion_mastery.by_summoner(server, summoner['id'])
    session["champion_mastery"] = champion_mastery

    # extract information from api data
    profileIcon_path = get_profile_picture(summoner_by_account)
    session["profileIcon_path"] = profileIcon_path

    mastery_list = get_mastery_list(champion_mastery)
    session["mastery_list"] = mastery_list

    main_champ = mastery_list[0][0]
    session["main_champ"] = main_champ

    level = get_level(summoner_by_account)
    session["level"] = level

    create_mastery_table(session["mastery_list"])

    # match history
    matchlist_by_account = flask_app.watcher.match.matchlist_by_account(server, summoner['accountId'])
    # get info from 5 last games
    match_id_history = get_match_id_history(matchlist_by_account, 5)
    data_last_matches, data_overview = get_stats_from_matchlist(server, summoner['name'], match_id_history)

    for j in range(len(match_id_history)):
        stats_last_matches = data_last_matches[j]['stats']
        timeline_last_matches = data_last_matches[j]['timeline']

        # save relevant info from these last few game_id_list
        champ_id = data_last_matches[j]['championId']
        champ = champion_id_to_name(champ_id)
        champ_session = "champ" + str(j)
        session[champ_session] = champ

        game_mode = data_overview[j][3]
        game_mode_session = "game_mode" + str(j)
        session[game_mode_session] = game_mode

        # epoch time to datetime conversion, divide by 1000 for ms
        game_start_epoch = data_overview[j][1] / 1000
        game_start = datetime.fromtimestamp(game_start_epoch).strftime('%Y-%m-%d %H:%M:%S')
        game_start_session = "game_start" + str(j)
        session[game_start_session] = game_start

        # get summoner spells e.g flicker and heal
        spells_used = [str(data_last_matches[j]['spell1Id']), str(data_last_matches[j]['spell2Id'])]
        spell_1, spell_2 = spell_id_to_name(spells_used)
        spell_1_session = "spell_1" + str(j)
        session[spell_1_session] = spell_1
        spell_2_session = "spell_2" + str(j)
        session[spell_2_session] = spell_2

        kills = stats_last_matches['kills']
        kills_session = "kills" + str(j)
        session[kills_session] = kills

        deaths = stats_last_matches['deaths']
        deaths_session = "deaths" + str(j)
        session[deaths_session] = deaths

        assists = stats_last_matches['assists']
        assists_session = "assists" + str(j)
        session[assists_session] = assists

        kda = str(kills) + " / " + str(deaths) + " / " + str(assists)
        kda_session = "kda" + str(j)
        session[kda_session] = kda

        true_dmg_dealt_champions = stats_last_matches['trueDamageDealtToChampions']
        true_dmg_dealt_champions_session = "true_dmg_dealt_champions" + str(j)
        session[true_dmg_dealt_champions_session] = true_dmg_dealt_champions

        total_dmg_dealt_champions = stats_last_matches['totalDamageDealtToChampions']
        total_dmg_dealt_champions_session = "total_dmg_dealt_champions" + str(j)
        session[total_dmg_dealt_champions_session] = total_dmg_dealt_champions

        physical_dmg_dealt_champions = stats_last_matches['physicalDamageDealtToChampions']
        physical_dmg_dealt_champions_session = "physical_dmg_dealt_champions" + str(j)
        session[physical_dmg_dealt_champions_session] = physical_dmg_dealt_champions

        magical_dmg_dealt_champions = stats_last_matches['magicDamageDealtToChampions']
        magical_dmg_dealt_champions_session = "magical_dmg_dealt_champions" + str(j)
        session[magical_dmg_dealt_champions_session] = magical_dmg_dealt_champions

        gold_earned = stats_last_matches['goldEarned']
        gold_earned_session = "gold_earned" + str(j)
        session[gold_earned_session] = gold_earned

        cs = stats_last_matches['totalMinionsKilled'] + stats_last_matches['neutralMinionsKilled']
        cs_session = "cs" + str(j)
        session[cs_session] = cs

        cs_avg_010_session = "cs_avg_010" + str(j)
        try:
            cs_avg_010 = timeline_last_matches['creepsPerMinDeltas']['0-10']
            session[cs_avg_010_session] = round(cs_avg_010, 1)
        except KeyError:
            session[cs_avg_010_session] = "N/A"

        cs_avg_1020_session = "cs_avg_1020" + str(j)
        try:
            cs_avg_1020 = timeline_last_matches['creepsPerMinDeltas']['10-20']
            session[cs_avg_1020_session] = round(cs_avg_1020, 1)
        except KeyError:
            session[cs_avg_1020_session] = "N/A"

        cs_vs_lane_010_session = "cs_vs_lane_010" + str(j)
        try:
            cs_vs_lane_010 = timeline_last_matches['csDiffPerMinDeltas']['0-10']
            session[cs_vs_lane_010_session] = round(cs_vs_lane_010, 1)
        except KeyError:
            session[cs_vs_lane_010_session] = "N/A"

        cs_vs_lane_1020_session = "cs_vs_lane_1020" + str(j)
        try:
            cs_vs_lane_1020 = timeline_last_matches['csDiffPerMinDeltas']['10-20']
            session[cs_vs_lane_1020_session] = round(cs_vs_lane_1020, 1)
        except KeyError:
            session[cs_vs_lane_1020_session] = "N/A"

        wards_placed_session = "wards_placed" + str(j)
        try:
            wards_placed = stats_last_matches['wardsPlaced']
            session[wards_placed_session] = wards_placed
        except KeyError:
            session[wards_placed_session] = "0"

        wards_killed_session = "wards_killed" + str(j)
        try:
            wards_killed = stats_last_matches['wardsKilled']
            session[wards_killed_session] = wards_killed
        except KeyError:
            session[wards_killed_session] = "0"

        item_ids = [str(stats_last_matches['item0']), str(stats_last_matches['item1']),
                     str(stats_last_matches['item2']), str(stats_last_matches['item3']),
                     str(stats_last_matches['item4']), str(stats_last_matches['item5']),
                     str(stats_last_matches['item6'])]
        items = item_id_to_name(item_ids)

        item0 = items[0]
        item0_session = "item0" + str(j)
        session[item0_session] = item0

        item1 = items[1]
        item1_session = "item1" + str(j)
        session[item1_session] = item1

        item2 = items[2]
        item2_session = "item2" + str(j)
        session[item2_session] = item2

        item3 = items[3]
        item3_session = "item3" + str(j)
        session[item3_session] = item3

        item4 = items[4]
        item4_session = "item4" + str(j)
        session[item4_session] = item4

        item5 = items[5]
        item5_session = "item5" + str(j)
        session[item5_session] = item5

    # live game overview
    try:
        data = flask_app.watcher.spectator.by_summoner(server, summoner['id'])
        table_1, table_2 = live_fetch_data(server, data, summoner['id'])
        session["table_1"] = table_1
        session["table_2"] = table_2
        session["vs"] = "vs"
    except:
        session["table_1"] = "This player is currently not in a game."
        session["table_2"] = ""
        session["vs"] = ""



def force_ascii(summoner_name):
    temp = normalize('NFKD', summoner_name).encode('ascii', 'ignore')
    return temp.decode('ascii')


def get_level(summoner_by_account):
    return summoner_by_account['summonerLevel']


def get_main_champ(champion_mastery):
    final_champion_mastery_list = get_mastery_list(champion_mastery)
    # champ with highest mastery e.g. Leblanc
    return final_champion_mastery_list[0][0]


def get_mastery_list(champion_mastery):
    champion_mastery_list = []
    for i in range(len(champion_mastery)):
        main_dic = champion_mastery[i]
        championId = main_dic['championId']
        champion_name = champion_id_to_name(championId)
        champion_mastery_list.append([champion_name])
    # add mastery values to the list of champions in your mastery list
    champion_mastery_list = add_mastery_values(champion_mastery_list, champion_mastery)
    # add available chests to the list
    champion_mastery_list = add_mastery_chest(champion_mastery_list, champion_mastery)
    # add champion level to the list
    champion_mastery_list = add_mastery_levels(champion_mastery_list, champion_mastery)
    return champion_mastery_list


def get_match_id_history(matchlist_by_account, amount_games):
    matches = matchlist_by_account['matches']
    game_id_list = []
    for i in matches:
        if amount_games == 0:
            return game_id_list

        game_id_list.append(i['gameId'])
        amount_games -= 1
    return game_id_list


def get_profile_picture(summoner_by_account):
    profileIcon_path = str(summoner_by_account['profileIconId']) + ".png"
    return profileIcon_path


def get_rank(summoner_info):
    return summoner_info['queueType'], summoner_info['tier'], summoner_info['rank']


def get_stats_from_matchlist(server, summonername, match_id_history):
    player_stats = []
    game_overview = []

    for i in match_id_history:
        match_info = flask_app.watcher.match.by_id(server, i)
        game_overview.extend([[match_info['gameId'], match_info['gameCreation'], match_info['gameDuration'], match_info['gameMode']]])

        players = match_info['participantIdentities']
        for j in players:
            player_info = j['player']
            if player_info['summonerName'] == summonername:
                participantid = j['participantId']
                temp = match_info['participants']
                for m in temp:
                    if isinstance(m, dict):
                        if 'participantId' in m:
                            if m['participantId'] == participantid:
                                player_stats.append(m)
    return player_stats, game_overview


def get_win_loss(summoner_info):
    wins = summoner_info['wins']
    losses = summoner_info['losses']
    return wins, losses, round((wins / (wins + losses)), 3)


def item_id_to_name(id_list):
    with open('static/dragontail-10.18.1/10.18.1/data/en_US/item.json', encoding="utf8") as f:
        data = json.load(f)
    data = data['data']
    items = []
    for i in id_list:
        if i == "0":
            items.append("N/A")
        else:
            for j in data.keys():
                if j == i:
                    items.append(data[j]['name'])
    return items


def last_played_champs(match_by_id):
    champs = []
    champ_id_list = []
    for i in range(len(match_by_id)):
        player_one = match_by_id['matches'][i]
        champ_player_one = player_one['champion']
        champ_name = champion_id_to_name(champ_player_one)
        champs.append([champ_name, player_one['gameId']])
        champ_id_list.append(champ_player_one)
    return champs, champ_id_list


def live_fetch_data(server, data, summonerId):

    game_overview = live_get_champs(server, data['participants'], summonerId)
    reduced_team1, reduced_team2 = reduce_game_overview(game_overview)
    table_1 = create_live_table(reduced_team1)
    table_2 = create_live_table(reduced_team2)
    return table_1, table_2


def live_get_champs(server, participants, summonerId):
    champs = []
    champs_uncleaned_names = []
    for i in participants:
        champs_uncleaned_names.append([[i['championId'], champion_id_to_name(i['championId'])],
        spell_id_to_name([str(i['spell1Id']), str(i['spell2Id'])]),
                        [i['summonerName'], i['summonerId']]])

        champs.append([[i['championId'], champion_id_to_name(i['championId'])],
                        spell_id_to_name([str(i['spell1Id']), str(i['spell2Id'])]),
                        [force_ascii(i['summonerName']), i['summonerId']]])

    for i, j in zip(champs, champs_uncleaned_names):
        mastery, account_level = live_get_summoner_champ_mastery(server, j[2][0], i[0][0], summonerId)
        summoner_info = flask_app.watcher.league.by_summoner(server, summonerId)[0]
        rank = summoner_info['tier'] + " " + summoner_info['rank']
        i[0].append(mastery)
        i[2].append(account_level)
        i[2].append(rank)

    return champs


def live_get_summoner_champ_mastery(server, name, champ_id, summonerId):

    summoner = flask_app.watcher.summoner.by_name(server, name)
    champion_mastery = flask_app.watcher.champion_mastery.by_summoner(server, summonerId)
    for i in champion_mastery:
        if i['championId'] == champ_id:
            return i['championPoints'], summoner['summonerLevel']


def pick_server(server):
    server = str(server)
    if server == "Brazil":
        return "br1"

    elif server == "Europe Nordic & East":
        return "eun1"

    elif server == "Europe West":
        return "euw1"

    elif server == "Japan":
        return "jp1"

    elif server == "Korea":
        return "kr"

    elif server == "Latin America North":
        return "la1"

    elif server == "Latin America South":
        return "la2"

    elif server == "North America":
        return "na1"

    elif server == "Oceania":
        return "oc1"

    elif server == "Russia":
        return "ru"

    elif server == "Turkey":
        return "tr1"

    else:
        return server


def rank_to_lowercase(list_a, return_string=False):
    final = []
    for i in list_a:
        x, y = i.split(" ", 1)
        x = x.lower()
        x = x.title()
        temp = x + " " + y
        final.append(temp)
    if return_string:
        return final[0]
    else:
        return final


def reduce_game_overview(game_overview):
    name = []
    champ = []
    spell_1 = []
    spell_2 = []
    rank = []
    mastery = []
    level = []
    for i in game_overview:
        name.append(i[2][0])
        champ.append(i[0][1])
        spell_1.append(i[1][0])
        spell_2.append(i[1][1])
        rank.append(i[2][3])
        mastery.append(i[0][2])
        level.append(i[2][2])

    rank_lower = rank_to_lowercase(rank)

    table_1 = [name[:5], champ[:5], spell_1[:5], spell_2[:5], rank_lower[:5], mastery[:5], level[:5]]
    table_2 = [name[5:], champ[5:], spell_1[5:], spell_2[5:], rank_lower[5:], mastery[5:], level[5:]]

    return table_1, table_2


def spell_id_to_name(spell_list):
    with open('static/dragontail-10.18.1/10.18.1/data/en_US/summoner.json', encoding="utf8") as f:
        data = json.load(f)
    for i in data.keys():
        if isinstance(data[i], dict):
            for j in data[i]:
                if data[i][j]['key'] == spell_list[0]:
                    spell_1 = data[i][j]['name']
                elif data[i][j]['key'] == spell_list[1]:
                    spell_2 = data[i][j]['name']
    return spell_1, spell_2
