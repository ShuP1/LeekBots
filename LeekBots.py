#!/usr/bin/env python
#Sheychen 2017
#CC BY

import sys
import random
import time
import os.path
import json
import itertools
import APILeekwars as API
from CommandTree import CommandTree

global lwapi
lwapi = API.APILeekwars()


class Settings:
    def __init__(self, options):
        self.filePath = options['path']
        if self.filePath.startswith('*/'):
            self.filePath = os.path.join(
                os.path.dirname(__file__), self.filePath[2:])
        self.settings = None
        self.get()

    def save(self):
        with open(self.filePath, 'w') as outfile:
            json.dump(self.settings, outfile)

    def get(self):
        if self.settings is None:
            self.settings = {'farmers': {}, 'pools': {'main': {}}}
            if os.path.exists(
                    self.filePath) and os.path.getsize(self.filePath) > 0:
                with open(self.filePath) as json_data_file:
                    js = json.load(json_data_file)
                    self.settings = js

        return self.settings

    def getFarmers(self):
        return self.get()['farmers']

    def addFarmer(self, id, login, password):
        if not self.settings['farmers'].get(str(id)) is None:
            raise ValueError('Farmer {0}: Allready added'.format(login))

        self.settings['farmers'][id] = {'login': login, 'password': password}
        self.save()

    def getPools(self):
        return self.get()['pools']

    def addPool(self, pool):
        if not self.settings['pools'].get(pool) is None:
            raise ValueError('Pool {0}: Allready added'.format(pool))

        self.settings['pools'][pool] = {}
        self.save()

    def addLeek(self, pool, id, farmer):
        if self.settings['pools'].get(pool) is None:
            raise ValueError('Pool {0}: Doesn\'t exists'.format(pool))
        if not self.settings['pools'][pool].get(str(id)) is None:
            raise ValueError('Leek {0}: Allready added in Pool {1}'.format(
                id, pool))

        self.settings['pools'][pool][id] = str(farmer)
        self.save()


class Items:
    weapons = None

    @staticmethod
    def getWeapons():
        if Items.weapons == None:
            Items.weapons = {}
            weapons = lwapi.weapon.get_all()['weapons']
            for weapon in weapons:
                Items.weapons[int(weapon)] = weapons[weapon]['name']
        return Items.weapons

    chips = None

    @staticmethod
    def getChips():
        if Items.chips == None:
            Items.chips = {}
            chips = lwapi.chip.get_all()['chips']
            for chip in chips:
                Items.chips[int(chip)] = chips[chip]['name']
        return Items.chips

    potions = None

    @staticmethod
    def getPotions():
        if Items.potions == None:
            Items.potions = {}
            potions = lwapi.potion.get_all()['potions']
            for potion in potions:
                Items.potions[int(potion)] = potions[potion]['name']
        return Items.potions

    @staticmethod
    def getAll():
        return {**Items.getWeapons(), **Items.getChips(), **Items.getPotions()}

    @staticmethod
    def getName(id):
        return Items.getAll().get(id, '?')

    @staticmethod
    def keyForValue(items, key):
        try:
            return list(items.keys())[list(items.values()).index(key)]
        except:
            raise ValueError('Unknown item "{0}"'.format(key))

    @staticmethod
    def toID(items, key):
        if key.isdigit():
            key = int(key)
            if not key in items:
                raise ValueError('Unknown item id "{0}"'.format(key))
            return key
        else:
            return Items.keyForValue(items, key)


class Farmers:
    @staticmethod
    def login(login, password):
        r = lwapi.farmer.login_token(login, password)
        if not r.get('success', False):
            raise ValueError('{0}: {1}'.format(login, r.get('error', 'Fail')))
        return Farmer(r)

    @staticmethod
    def farmer(settings, id):
        login = settings.getFarmers().get(id)
        if login is None:
            raise ValueError('Can\'t find Farmer "{0}"'.format(id))
        return Farmers.login(login['login'], login['password'])

    @staticmethod
    def farmerIn(settings, ids):
        for id in ids:
            login = settings.getFarmers().get(id)
            if not login is None:
                return Farmers.login(login['login'], login['password'])
        raise ValueError('Can\'t find any farmer')

    @staticmethod
    def parse(options):
        farmer = options.get('farmer')
        if farmer is None:
            raise ValueError('Any farmer option (use -f <id>)')
        print('Using "{0}" farmer'.format(farmer))
        return farmer

    @staticmethod
    def get(settings):
        farmers = []
        logins = settings.getFarmers()
        for id in logins:
            try:
                farmers.append(
                    Farmers.login(logins[id]['login'], logins[id]['password']))
            except ValueError as err:
                print(format(err))
        return farmers

    @staticmethod
    def list(params, options):
        mode = params[0]
        if mode is None:
            farmers = Settings(options).getFarmers()
            for farmer in farmers:
                print('{0}: {1}'.format(farmer, farmers[farmer]['login']))
        else:
            for farmer in Farmers.get(Settings(options)):
                print('{0}:'.format(farmer.name))
                if mode == 'infos':
                    for field in ['id', 'talent', 'fights', 'habs']:
                        print('  {0} : {1}'.format(field, farmer.data[field]))
                elif mode == 'ais':
                    for ai in farmer.getAis():
                        print('  {0} : {1}'.format(ai['name'], ai['id']))
                elif mode == 'stuff':
                    print('  {0}'.format(', '.join(
                        str(item['template'])
                        for item in farmer.weapons + farmer.chips)))
                elif mode == 'leeks':
                    for id in farmer.leeks:
                        print('  {0} : {1} ({2}, {3})'.format(
                            id, farmer.leeks[id]['name'],
                            farmer.leeks[id]['level'],
                            farmer.leeks[id]['talent']))

    @staticmethod
    def stats(params, options):
        print('Deprecated: use "pool stats"')
        mode = params[0]
        if mode == 'infos':
            fields = {'talent': [], 'fights': [], 'habs': []}
        for farmer in Farmers.get(Settings(options)):
            for field in fields:
                fields[field].append(farmer.data[field])
        print('value : min, avg, max')
        for field in fields:
            print('{0} : {1}, {2}, {3}'.format(
                field, min(fields[field]),
                int(sum(fields[field]) / len(fields[field])),
                max(fields[field])))

    @staticmethod
    def register(params, options):
        login = params[0]
        password = params[1]
        try:
            farmer = Farmers.login(login, password)
            Settings(options).addFarmer(farmer.id, login, password)
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def buy(params, options):
        item = params[0]
        for farmer in Farmers.get(Settings(options)):
            try:
                for x in (farmer.chips + farmer.weapons):
                    if x['template'] == item:
                        farmer.raiseError('Allready have one')

                farmer.buy(item)
                farmer.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    @staticmethod
    def sell(params, options):
        item = params[0]
        for farmer in Farmers.get(Settings(options)):
            try:
                farmer.sell(item)
                farmer.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    @staticmethod
    def tournament(params, options):
        try:
            farmer = Farmers.farmer(Settings(options), Farmers.parse(options))
            farmer.tournament()
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def fight(params, options):
        try:
            random.seed()
            farmer = Farmers.farmer(Settings(options), Farmers.parse(options))
            for _ in range(params[0] if type(params[0]) is int else 20):
                opponents = farmer.getOpponents()
                if len(opponents) < 1:
                    farmer.raiseError('Probably, no more farmer fights')

                if options['selection-mode'] == 'random':
                    opid = random.choice(opponents)['id']
                else:
                    opid = None
                    if options['selection-mode'] == 'worst':
                        optalent = 20000000
                    else:
                        optalent = 0
                    for x in opponents:
                        if (options['selection-mode'] == 'worst'
                                and optalent > x['talent']) or (
                                    not options['selection-mode'] == 'worst'
                                    and optalent < x['talent']):
                            opid = x['id']
                            optalent = x['talent']

                print('https://leekwars.com/fight/{0}'.format(
                    farmer.fight(opid)))
                time.sleep(options['sleep'])
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def createLeek(params, options):
        name = params[0]
        try:
            farmer = Farmers.farmer(Settings(options), Farmers.parse(options))
            farmer.createLeek(name)
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def twelve(params, options):
        try:
            farmer = Farmers.farmer(Settings(options), Farmers.parse(options))
            buys = {}
            for item in farmer.market().values():
                buys['buy ' + item['name']] = -item['price_habs']

            targetHabs = 121212 - farmer.habs

            itemsCount = 0
            haveTooMuch = True
            while haveTooMuch:
                print('With ' + str(itemsCount) + ' items')
                haveTooMuch = False
                for combination in itertools.combinations_with_replacement(
                        buys, itemsCount):
                    currentHabs = sum(buys[op] for op in combination)
                    if currentHabs == targetHabs:
                        print(combination)
                        return
                    elif currentHabs > targetHabs:
                        haveTooMuch = True
                itemsCount += 1

            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def rankingLeeks(params, options):
        try:
            leeks = {}
            for farmer in Farmers.get(Settings(options)):
                for leek in farmer.leeks.values():
                    leeks[leek['name']] = leek['talent']

            for w in sorted(leeks, key=leeks.get, reverse=True):
                print(w, str(leeks[w]))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def ranking(params, options):
        try:
            farmers = {}
            for farmer in Farmers.get(Settings(options)):
                farmers[farmer.name] = farmer.talent

            for w in sorted(farmers, key=farmers.get, reverse=True):
                print(w, str(farmers[w]))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def rankingTeams(params, options):
        try:
            teams = {}
            for farmer in Farmers.get(Settings(options)):
                team = Team.get(farmer.data['team']['id'])
                teams[team['name']] = team['talent']

            for w in sorted(teams, key=teams.get, reverse=True):
                print(w, str(teams[w]))
        except ValueError as err:
            print(format(err))


class Pools:
    @staticmethod
    def list(params, options):
        print('TODO add params (leeks, ...)')
        print(', '.join(Settings(options).getPools()))


class Pool:
    @staticmethod
    def parse(options):
        pool = options.get('pool', 'main')
        print('Using "{0}" pool'.format(pool))
        return pool

    @staticmethod
    def get(settings, pid):
        pool = settings.getPools().get(pid)
        farmers = settings.getFarmers()
        if pool is None:
            raise ValueError('Pool {0}: Doesn\'t exists'.format(pid))
        leeks = []
        for leek in pool:
            try:
                leeks.append(
                    Farmers.login(
                        farmers[pool[leek]]['login'],
                        farmers[pool[leek]]['password']).getLeek(leek))
            except ValueError as err:
                print(format(err))
        return leeks

    @staticmethod
    def create(params, options):
        try:
            Settings(options).addPool(Pool.parse(options))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def register(params, options):
        try:
            pool = Pool.parse(options)
            lid = params[0]
            fid = None
            for farmer in Farmers.get(Settings(options)):
                if lid in farmer.leeks:
                    fid = farmer.id
            if fid is None:
                raise ValueError(
                    'Any register farmer for leek "{0}"'.format(lid))
            Settings(options).addLeek(pool, lid, fid)
            print('OK')
        except ValueError as err:
            print(format(err))

    @staticmethod
    def list(params, options):
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                print(leek.name)
                if len(params) == 1:
                    mode = params[0]
                    if mode == 'infos':
                        for field in ['id', 'talent', 'level']:
                            print('  {0} : {1}'.format(field,
                                                       leek.data[field]))
                        print('  fights : {0}'.format(leek.farmer.fights))
                    elif mode == 'stuff':
                        for item in leek.weapons + leek.chips:
                            print('  {0}'.format(item['template']))
                    elif mode == 'characteristics':
                        for field in [
                                'life', 'strength', 'wisdom', 'agility',
                                'resistance', 'science', 'magic', 'tp', 'mp',
                                'frequency', 'capital'
                        ]:
                            print('  {0} : {1}'.format(field,
                                                       leek.data[field]))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def stats(params, options):
        mode = params[0]
        if mode == 'infos':
            fields = {'talent': [], 'level': []}
        elif mode == 'farmers':
            fields = {'fights': [], 'habs': []}
        elif mode == 'characteristics':
            fields = {
                'life': [],
                'strength': [],
                'wisdom': [],
                'agility': [],
                'resistance': [],
                'science': [],
                'magic': [],
                'tp': [],
                'mp': [],
                'frequency': [],
                'capital': []
            }
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                for field in fields:
                    fields[field].append(leek.data[field] if mode != 'farmers'
                                         else leek.farmer.data[field])
        except ValueError as err:
            print(format(err))
        print('value : min, avg, max')
        for field in fields:
            print('{0} : {1}, {2}, {3}'.format(
                field, min(fields[field]),
                int(sum(fields[field]) / len(fields[field])),
                max(fields[field])))

    @staticmethod
    def items(params, options):
        mode = params[0]
        items = {}
        if mode == None:
            mode = 'all'
        try:
            i = 0
            leeks = Pool.get(Settings(options), Pool.parse(options))
            for leek in leeks:
                itemList = []
                if mode == 'all' or mode == 'weapons':
                    itemList += leek.farmer.weapons
                if mode == 'all' or mode == 'chips':
                    itemList += leek.farmer.chips
                if mode == 'all' or mode == 'potions':
                    itemList += leek.farmer.potions
                for item in itemList:
                    if not item['template'] in items:
                        items[item['template']] = [0] * len(leeks)
                    items[item['template']][i] += 1
                i += 1
        except ValueError as err:
            print(format(err))
        print('item : min, avg, max')
        for field in items:
            print('{0} : {1}, {2}, {3}'.format(
                Items.getName(field), min(items[field]),
                int(sum(items[field]) / len(items[field])), max(items[field])))

    @staticmethod
    def fight(params, options):
        try:
            random.seed()
            leeks = Pool.get(Settings(options), Pool.parse(options))
            leeksids = [x.id for x in leeks]
            random.shuffle(leeks)
            force = (params[1] == 'force')
            for leek in leeks:
                try:
                    fights = params[0] if type(
                        params[0]) is int else leek.farmer.fights
                    if fights < 1:
                        leek.raiseError('No more fights')

                    for _ in range(fights):
                        opponents = leek.getOpponents()
                        if len(opponents) < 1:
                            leek.raiseError('Probably, no more fights')

                        if options['selection-mode'] == 'random':
                            oplist = [
                                x['id'] for x in opponents
                                if force or not x['id'] in leeksids
                            ]

                            if len(oplist) < 1:
                                leek.raiseError(
                                    'Really? All your opponnents are allies')
                            opid = random.choice(oplist)
                        else:
                            opid = None
                            if options['selection-mode'] == 'worst':
                                opscore = 20000000
                            else:
                                opscore = 0
                            for x in opponents:
                                if force or not x['id'] in leeksids:
                                    score = x['level'] * x['talent']
                                    if (options['selection-mode'] == 'worst'
                                            and score < opscore
                                        ) or (not options['selection-mode'] ==
                                              'worst' and score > opscore):
                                        opid = x['id']
                                        opscore = score
                            if opid is None:
                                leek.raiseError(
                                    'Really? All your opponnents are allies')

                        print('https://leekwars.com/fight/{0}'.format(
                            leek.fight(opid)))
                        time.sleep(options['sleep'])
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def setupAI(params, options):
        try:
            pool = Pool.parse(options)
            path = os.path.join('ai', pool)
            if not os.path.exists(path):
                raise ValueError('Can\'t find "{0}" folder'.format(path))

            ais = {}
            for fileName in os.listdir(path):
                if fileName.endswith('.leek'):
                    with open(os.path.join(path, fileName), 'r') as myfile:
                        ais[pool + '-' + fileName[:-5]] = myfile.read()

            if (ais.get(pool + '-AI') is None):
                raise ValueError('Can\'t find "{0}/AI.leek" file'.format(path))

            for leek in Pool.get(Settings(options), pool):
                try:
                    fais = leek.farmer.getAis()
                    for ai in ais:
                        try:
                            aid = None
                            for current in fais:
                                if current['name'] == ai:
                                    aid = current['id']
                                    break

                            if aid is None:
                                print('New ai "{0}" for {1}'.format(
                                    ai, leek.farmer.name))
                                aid = leek.farmer.newAi(0, ai)['id']

                            leek.farmer.saveAi(aid, ais[ai])
                            if ai == pool + '-AI':
                                leek.setAi(aid)
                        except ValueError as err:
                            print(format(err))
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def tournament(params, options):
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.tournament()
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def equipWeapon(params, options):
        try:
            template = Items.toID(Items.getWeapons(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    wid = None
                    for weapon in leek.farmer.weapons:
                        if (weapon['template'] == template):
                            wid = weapon['id']

                    if wid is None:
                        if options['buy']:
                            print(leek.farmer.name + ' buy')
                            wid = leek.farmer.buy(template)
                        else:
                            leek.farmer.raiseError(
                                'Have any {0} available. (use --buy)'.format(
                                    template))

                    leek.equipWeapon(wid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def unequipWeapon(params, options):
        try:
            template = Items.toID(Items.getWeapons(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    wid = None
                    for weapon in leek.weapons:
                        if (weapon['template'] == template):
                            wid = weapon['id']

                    if wid is None:
                        leek.farmer.raiseError(
                            'Have any {0} available'.format(template))

                    leek.unequipWeapon(wid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def equipChip(params, options):
        try:
            template = Items.toID(Items.getChips(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    wid = None
                    for chip in leek.farmer.chips:
                        if (chip['template'] == template):
                            wid = chip['id']

                    if wid is None:
                        if options['buy']:
                            print(leek.farmer.name + ' buy')
                            wid = leek.farmer.buy(template)
                        else:
                            leek.farmer.raiseError(
                                'Have any {0} available. (use --buy)'.format(
                                    template))

                    leek.equipChip(wid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def unequipChip(params, options):
        try:
            template = Items.toID(Items.getChips(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    wid = None
                    for chip in leek.chips:
                        if (chip['template'] == template):
                            wid = chip['id']

                    if wid is None:
                        leek.farmer.raiseError(
                            'Have any {0} available'.format(template))

                    leek.unequipChip(wid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def usePotion(params, options):
        try:
            template = Items.toID(Items.getPotions(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    pid = None
                    for potion in leek.farmer.potions:
                        if (potion['template'] == template):
                            pid = potion['id']

                    if pid is None:
                        if options['buy']:
                            print(leek.farmer.name + ' buy')
                            pid = leek.farmer.buy(template)
                        else:
                            leek.farmer.raiseError(
                                'Have any {0} available. (use --buy)'.format(
                                    template))

                    leek.usePotion(pid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def buy(params, options):
        try:
            item = Items.toID(Items.getAll(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    for x in (leek.farmer.chips + leek.farmer.weapons):
                        if x['template'] == item:
                            leek.farmer.raiseError('Allready have one')

                    leek.farmer.buy(item)
                    leek.farmer.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def sell(params, options):
        try:
            item = Items.toID(Items.getAll(), params[0])
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.farmer.sell(item)
                    leek.farmer.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def characteristics(params, options):
        bonuses = {
            'life': 0,
            'strength': 0,
            'wisdom': 0,
            'agility': 0,
            'resistance': 0,
            'frequency': 0,
            'science': 0,
            'magic': 0,
            'tp': 0,
            'mp': 0
        }
        bonuses[params[1]] = params[0]
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.characteristics(bonuses)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def teamJoin(params, options):
        team = params[0]
        try:
            owner = Farmers.farmer(Settings(options), Team.getOwner(team))
            owner.openTeam('true')
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.farmer.joinTeam(team)
                    for candidacy in owner.getTeam(team)['candidacies']:
                        if candidacy['farmer']['id'] == leek.farmer.id:
                            owner.acceptTeamCandidacy(candidacy['id'])
                            leek.raiseError('OK')  #Ugly
                    leek.raiseError('Can\'t find candidacy')  #Ugly
                except ValueError as err:
                    print(format(err))
            owner.openTeam('false')
        except ValueError as err:
            print(format(err))

    @staticmethod
    def teamComposition(params, options):
        try:
            leeks = Pool.get(Settings(options), Pool.parse(options))
            team = leeks[0].farmer.data['team']['id']
            owner = Farmers.farmerIn(Settings(options), Team.getCaptains(team))
            composition = owner.createTeamComposition(params[0])['id']
            for leek in leeks:
                try:
                    owner.setTeamComposition(composition, leek.id)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
            for compo in owner.getTeam(team)['compositions']:
                if len(compo['leeks']) == 0:
                    owner.removeTeamComposition(compo['id'])
        except ValueError as err:
            print(format(err))

    @staticmethod
    def teamTournament(params, options):
        try:
            leek = Pool.get(Settings(options), Pool.parse(options))[0]
            team = leek.farmer.data['team']['id']
            owner = Farmers.farmerIn(Settings(options), Team.getCaptains(team))
            for composition in owner.getTeam(team)['compositions']:
                cleeks = [x['id'] for x in composition['leeks']]
                if leek.id in cleeks:
                    owner.tournamentTeamComposition(composition['id'])
                    leek.raiseError('OK')  #Ugly
            leek.raiseError('Can\'t find composition')
        except ValueError as err:
            print(format(err))

    @staticmethod
    def teamEmblem(params, options):
        try:
            leek = Pool.get(Settings(options), Pool.parse(options))[0]
            team = leek.farmer.data['team']['id']
            owner = Farmers.farmerIn(Settings(options), Team.getCaptains(team))
            owner.teamEmblem(team, open(params[0], 'rb'))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def teamFight(params, options):
        try:
            random.seed()
            leek = Pool.get(Settings(options), Pool.parse(options))[0]
            team = leek.farmer.data['team']['id']
            for composition in leek.farmer.getTeam(team)['compositions']:
                cleeks = [x['id'] for x in composition['leeks']]
                if leek.id in cleeks:
                    cid = composition['id']
                    for _ in range(params[0]
                                   if type(params[0]) is int else 20):
                        opponents = leek.getCompositionOpponents(cid)
                        if len(opponents) < 1:
                            leek.raiseError('Probably, no more team fights')

                        if options['selection-mode'] == 'random':
                            opid = random.choice(opponents)['id']
                        else:
                            opid = None
                            if options['selection-mode'] == 'worst':
                                optalent = 20000000
                            else:
                                optalent = 0
                            for x in opponents:
                                if (
                                        options['selection-mode'] == 'worst'
                                        and optalent > x['talent']
                                ) or (not options['selection-mode'] == 'worst'
                                      and optalent < x['talent']):
                                    opid = x['id']
                                    optalent = x['talent']

                        print('https://leekwars.com/fight/{0}'.format(
                            leek.teamFight(cid, opid)))
                        time.sleep(options['sleep'])
                    leek.raiseError('OK')  #Ugly
            leek.raiseError('Can\'t find composition')
        except ValueError as err:
            print(format(err))

    @staticmethod
    def auto(params, options):
        Pool.fight([None, None], options)
        Pool.fight([None, 'force'], options)
        time.sleep(options['sleep'] * 10)
        Pool.teamFight([None], options)
        Pool.tournament([], options)
        Pool.teamTournament([], options)

    @staticmethod
    def farmersTournament(params, options):
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.farmer.tournament()
                    leek.farmer.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    @staticmethod
    def farmersAvatar(params, options):
        try:
            for leek in Pool.get(Settings(options), Pool.parse(options)):
                try:
                    leek.farmer.avatar(open(params[0], 'rb'))
                    leek.farmer.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))


class Team:
    @staticmethod
    def create(params, options):
        name = params[0]
        try:
            farmer = Farmers.farmer(Settings(options), Farmers.parse(options))
            farmer.createTeam(name)
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    @staticmethod
    def get(team):
        req = lwapi.team.get(team)
        if not req.get('success', False):
            raise ValueError('Team {0} : {1}'.format(team,
                                                     req.get('error', 'Fail')))
        return req['team']

    @staticmethod
    def getOwner(team):
        for member in Team.get(team)['members']:
            if member['grade'] == 'owner':
                return str(member['id'])
        raise ValueError('Team {0} : Can\'t find owner'.format(team))

    @staticmethod
    def getCaptains(team):
        captains = []
        for member in Team.get(team)['members']:
            if member['grade'] in ['owner', 'captain']:
                captains.append(str(member['id']))
        return captains


class Farmer:
    def __init__(self, data):
        self.data = data['farmer']
        self.token = data['token']

        self.id = self.data['id']
        self.name = self.data['name']
        self.habs = self.data['habs']
        self.weapons = self.data['weapons']
        self.chips = self.data['chips']
        self.potions = self.data['potions']
        self.leeks = self.data['leeks']
        self.fights = self.data['fights']
        self.talent = self.data['talent']

    def raiseError(self, error):
        raise ValueError('Farmer {0} : {1}'.format(self.name, error))

    def checkRequest(self, req):
        if not req.get('success', False):
            self.raiseError(req.get('error', 'Fail'))
        return req

    def buy(self, item):
        return self.checkRequest(lwapi.market.buy_habs(item,
                                                       self.token))['item']

    def sell(self, item):
        self.checkRequest(lwapi.market.sell_habs(item, self.token))

    def market(self):
        return self.checkRequest(lwapi.market.get_item_templates(
            self.token))['items']

    def getLeek(self, leek):
        return Leek(
            self.checkRequest(lwapi.leek.get_private(leek, self.token)), self)

    def getOpponents(self):
        return self.checkRequest(
            lwapi.garden.get_farmer_opponents(self.token))['opponents']

    def getAis(self):
        return self.checkRequest(lwapi.ai.get_farmer_ais(self.token))['ais']

    def newAi(self, folder, name):
        ai = self.checkRequest(lwapi.ai.new(folder, 'false', self.token))['ai']
        self.checkRequest(lwapi.ai.rename(ai['id'], name, self.token))
        return ai

    def saveAi(self, ai, script):
        ai = self.checkRequest(lwapi.ai.save(ai, script, self.token))['result']
        if len(ai[0]) > 3:
            self.raiseError('Script error (' + ', '.join(
                str(x) for x in ai[0][3:]) + ')')

    def joinTeam(self, team):
        self.checkRequest(lwapi.team.send_candidacy(team, self.token))

    def openTeam(self, open):
        self.checkRequest(lwapi.team.set_opened(open, self.token))

    def createTeam(self, name):
        self.checkRequest(lwapi.team.create(name, self.token))
        self.openTeam('false')

    def getTeam(self, team):
        return self.checkRequest(lwapi.team.get_private(team,
                                                        self.token))['team']

    def acceptTeamCandidacy(self, candidacy):
        self.checkRequest(lwapi.team.accept_candidacy(candidacy, self.token))

    def createTeamComposition(self, composition):
        return self.checkRequest(
            lwapi.team.create_composition(composition, self.token))

    def setTeamComposition(self, composition, leek):
        self.checkRequest(lwapi.team.move_leek(leek, composition, self.token))

    def removeTeamComposition(self, composition):
        self.checkRequest(
            lwapi.team.delete_composition(composition, self.token))

    def tournamentTeamComposition(self, composition):
        self.checkRequest(
            lwapi.team.register_tournament(composition, self.token))

    def tournament(self):
        self.checkRequest(lwapi.farmer.register_tournament(self.token))

    def fight(self, target):
        return self.checkRequest(
            lwapi.garden.start_farmer_fight(target, self.token))

    def avatar(self, avatar):
        return self.checkRequest(lwapi.farmer.set_avatar(avatar, self.token))

    def teamEmblem(self, team, emblem):
        return self.checkRequest(
            lwapi.team.set_emblem(team, emblem, self.token))

    def createLeek(self, name):
        return self.checkRequest(lwapi.leek.create(name, self.token))

    def getFirstLeekId(self):
        #NOTE: Deprecated
        return next(iter(self.leeks))


class Leek:
    def __init__(self, data, farmer):
        self.data = data['leek']
        self.farmer = farmer

        self.id = self.data['id']
        self.name = self.data['name']
        self.weapons = self.data['weapons']
        self.chips = self.data['chips']

    def raiseError(self, error):
        raise ValueError('Leek {0} : {1}'.format(self.name, error))

    def checkRequest(self, req):
        if not req.get('success', False):
            self.raiseError(req.get('error', 'Fail'))
        return req

    def getOpponents(self):
        return self.checkRequest(
            lwapi.garden.get_leek_opponents(self.id,
                                            self.farmer.token))['opponents']

    def fight(self, target):
        return self.checkRequest(
            lwapi.garden.start_solo_fight(self.id, target,
                                          self.farmer.token))['fight']

    def setAi(self, ai):
        self.checkRequest(lwapi.leek.set_ai(self.id, ai, self.farmer.token))

    def tournament(self):
        self.checkRequest(
            lwapi.leek.register_tournament(self.id, self.farmer.token))

    def equipWeapon(self, wid):
        self.checkRequest(
            lwapi.leek.add_weapon(self.id, wid, self.farmer.token))

    def unequipWeapon(self, wid):
        self.checkRequest(lwapi.leek.remove_weapon(wid, self.farmer.token))

    def equipChip(self, wid):
        self.checkRequest(lwapi.leek.add_chip(self.id, wid, self.farmer.token))

    def unequipChip(self, wid):
        self.checkRequest(lwapi.leek.remove_chip(wid, self.farmer.token))

    def usePotion(self, pid):
        self.checkRequest(
            lwapi.leek.use_potion(self.id, pid, self.farmer.token))

    def characteristics(self, bonuses):
        self.checkRequest(
            lwapi.leek.spend_capital(self.id, json.dumps(bonuses),
                                     self.farmer.token))

    def getCompositionOpponents(self, composition):
        return self.checkRequest(
            lwapi.garden.get_composition_opponents(
                composition, self.farmer.token))['opponents']

    def teamFight(self, composition, target):
        return self.checkRequest(
            lwapi.garden.start_team_fight(composition, target,
                                          self.farmer.token))['fight']


# Main Program
if __name__ == "__main__":
    CommandTree()\
    .addOption('pool', ['p', '-pool'], {'name': 'pool', 'optional': True, 'default': 'main'})\
    .addOption('farmer', ['f', '-farmer'], {'name': 'farmer (id)', 'optional': True})\
    .addOption('selection-mode', ['sm', '-selection-mode'], {'name': 'selection mode', 'optional': True, 'list': ['random', 'best', 'worst'], 'default': 'worst'})\
    .addOption('sleep', ['s', '-sleep'], {'name': 'sleep time', 'optional': True, 'type': int, 'min': 0, 'default': 1})\
    .addOption('buy', ['b', '-buy'], {'name': 'should buy', 'optional': True, 'type': bool, 'default': False})\
    .addOption('path', ['-path'], {'name': 'config path', 'optional': True, 'default': '*/LeekBots.json'})\
    .addCommand('farmers list', 'list all farmers', Farmers.list, [{'name': 'mode', 'optional': True, 'list': [None, 'infos', 'ais', 'stuff', 'leeks']}])\
    .addCommand('farmers stats', 'stats of all farmers', Farmers.stats, [{'name': 'mode', 'list': ['infos']}])\
    .addCommand('farmers buy', 'buy an item FOREACH farmers',Farmers.buy, [{'name': 'item', 'type': int}])\
    .addCommand('farmers sell', 'sell an item FOREACH farmers',Farmers.sell, [{'name': 'item', 'type': int}])\
    .addCommand('farmer register', 'add a new farmer',Farmers.register, [{'name': 'login'},{'name': 'password'}])\
    .addCommand('farmer fight', 'run farmer fights', Farmers.fight, [{'name': 'count', 'optional': True, 'type': int, 'min': 1, 'max': 20}])\
    .addCommand('farmer tournament', 'register farmer to tournament', Farmers.tournament, [])\
    .addCommand('farmer create leek', 'create a new leek for farmer', Farmers.createLeek, [{'name': 'name'}])\
    .addCommand('farmer twelve', 'helper', Farmers.twelve, [])\
    .addCommand('pools list', 'list all pools',Pools.list, [])\
    .addCommand('pool create', 'create a new pool',Pool.create, [])\
    .addCommand('pool register', 'add a leek to a pool',Pool.register, [{'name': 'leek'}])\
    .addCommand('pool list', 'list leeks',Pool.list, [{'name': 'mode', 'optional': True, 'list': [None, 'infos', 'stuff', 'characteristics']}])\
    .addCommand('pool stats', 'stats of pool\'s leeks', Pool.stats, [{'name': 'mode', 'list': ['infos', 'characteristics', 'farmers']}])\
    .addCommand('pool items', 'list farmer\'s items', Pool.items, [{'name': 'mode', 'optional': True, 'list': ['all', 'potions', 'weapons', 'chips']}])\
    .addCommand('pool fight', 'run solo fights', Pool.fight, [{'name': 'count', 'optional': True, 'type': int, 'min': 1, 'max': 100}, {'name': 'force', 'optional': True, 'list': [None, 'force']}])\
    .addCommand('pool ais', 'import ai/<pool>/<name>.leek files and load ai/<pool>/AI.leek', Pool.setupAI, [])\
    .addCommand('pool tournament', 'register for solo tournament', Pool.tournament, [])\
    .addCommand('pool equip weapon', 'equip a weapon', Pool.equipWeapon, [{'name': 'item'}])\
    .addCommand('pool unequip weapon', 'unequip a weapon', Pool.unequipWeapon, [{'name': 'item'}])\
    .addCommand('pool equip chip', 'equip a chip', Pool.equipChip, [{'name': 'item'}])\
    .addCommand('pool unequip chip', 'unequip a chip', Pool.unequipChip, [{'name': 'item'}])\
    .addCommand('pool use potion', 'use a potion', Pool.usePotion, [{'name': 'potion'}])\
    .addCommand('pool characteristics', 'buy characteristics', Pool.characteristics, [{'name': 'count', 'type': int}, {'name': 'type', 'list': ['life', 'strength', 'wisdom', 'agility', 'resistance', 'science', 'magic', 'tp', 'mp', 'frequency']}])\
    .addCommand('pool buy', 'buy an item', Pool.buy, [{'name': 'item'}])\
    .addCommand('pool sell', 'sell an item', Pool.sell, [{'name': 'item'}])\
    .addCommand('pool team join', 'join a team. owner must be register', Pool.teamJoin, [{'name': 'team', 'type': int}])\
    .addCommand('pool team composition', 'create a composition. a captain must be register', Pool.teamComposition, [{'name': 'composition'}])\
    .addCommand('pool team tournament', 'register composition for team tournament. based on first farmer team', Pool.teamTournament, [])\
    .addCommand('pool team fight', 'run team fights', Pool.teamFight, [{'name': 'count', 'optional': True, 'type': int, 'min': 1, 'max': 20}])\
    .addCommand('pool team emblem', 'set emblem', Pool.teamEmblem, [{'name': 'file'}])\
    .addCommand('pool farmers avatar', 'set avatar for each farmer', Pool.farmersAvatar, [{'name': 'file'}])\
    .addCommand('pool farmers tournament', 'register each farmer to tournament', Pool.farmersTournament, [])\
    .addCommand('pool auto', 'run "fight, fight force, team fight, tournament, team tournament"', Pool.auto, [])\
    .addCommand('team create', 'create a team', Team.create, [{'name': 'name'}, {'name': 'owner'}])\
    .addCommand('ranking leeks', 'get ranking of all leeks', Farmers.rankingLeeks, [])\
    .addCommand('ranking farmers', 'get ranking of all farmers', Farmers.ranking, [])\
    .addCommand('ranking teams', 'get ranking of all farmers', Farmers.rankingTeams, [])\
    .parse(sys.argv)
