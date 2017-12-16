#!/usr/bin/env python
#Sheychen 2017
#CC BY

import sys
import random
import os.path
import json
import APILeekwars as API
from CommandTree import CommandTree

global lwapi
lwapi = API.APILeekwars()


class Settings:
    def __init__(self):
        self.filePath = 'LeekBots.json'
        self.settings = None
        self.get()

    def save(self):
        with open(self.filePath, 'w') as outfile:
            json.dump(self.settings, outfile)

    def get(self):
        if self.settings is None:
            self.settings = {'farmers': {}}
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

        self.settings['farmers'][id] = {
            'login': login,
            'password': password
        }
        self.save()


class Farmers:
    def login(login, password):
        r = lwapi.farmer.login_token(login, password)
        if not r.get('success', False):
            raise ValueError('{0}: {1}'.format(login, r.get('error', 'Fail')))
        return Farmer(r)

    def get():
        farmers = []
        logins = Settings().getFarmers()
        for id in logins:
            try:
                farmers.append(
                    Farmers.login(logins[id]['login'], logins[id]['password']))
            except ValueError as err:
                print(format(err))
        return farmers

    def list(options):
        mode = options[0]
        if mode is None:
            farmers = Settings().getFarmers()
            for farmer in farmers:
                print('{0}: {1}'.format(farmer, farmers[farmer]['login']))
        else:
            for farmer in Farmers.get():
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

    def stats(options):
        print('Deprecated: use "pool stats"')
        mode = options[0]
        if mode == 'infos':
            fields = {'talent': [], 'fights': [], 'habs': []}
        for farmer in Farmers.get():
            for field in fields:
                fields[field].append(farmer.data[field])
        print('value : min, avg, max')
        for field in fields:
            print('{0} : {1}, {2}, {3}'.format(field, min(
                fields[field]), int(sum(fields[field]) / len(fields[field])),
                                               max(fields[field])))

    def register(options):
        login = options[0]
        password = options[1]
        try:
            farmer = Farmers.login(login, password)
            Settings().addFarmer(farmer.id, login, password)
            farmer.raiseError('OK')  #Ugly
        except ValueError as err:
            print(format(err))

    def buy(options):
        item = options[0]
        for farmer in Farmers.get():
            try:
                for x in (farmer.chips + farmer.weapons):
                    if x['template'] == item:
                        farmer.raiseError('Allready have one')

                farmer.buy(item)
                farmer.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def sell(options):
        item = options[0]
        for farmer in Farmers.get():
            try:
                farmer.sell(item)
                farmer.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))


class FirstLeeks:
    def fight(options):
        print('Deprecated: use "pool fight"')
        #NOTE: In pools use pool's ids and not name.startswith
        random.seed()
        farmers = Farmers.get()
        random.shuffle(farmers)
        for farmer in farmers:
            try:
                fights = options[0] if type(
                    options[0]) is int else farmer.fights
                if fights < 1:
                    farmer.raiseError('No more fights')

                leek = farmer.getLeek(farmer.getFirstLeekId())
                for _ in range(fights):
                    opponents = leek.getOpponents()
                    if len(opponents) < 1:
                        leek.raiseError('Probably no more fights')

                    opponents = [
                        x['id'] for x in opponents
                        if options[1] == 'force'
                        or not x['name'].startswith('LeekBots')
                    ]
                    if len(opponents) < 1:
                        leek.raiseError(
                            'Really? All your opponnents are allies')

                    print('https://leekwars.com/fight/{0}'.format(
                        leek.fight(random.choice(opponents))))
            except ValueError as err:
                print(format(err))

    def list(options):
        print('Deprecated: use "pool list"')
        for farmer in Farmers.get():
            try:
                leek = farmer.getLeek(farmer.getFirstLeekId())
                print(leek.name)
                if len(options) == 1:
                    mode = options[0]
                    if mode == 'infos':
                        for field in ['id', 'talent', 'level']:
                            print('  {0} : {1}'.format(field,
                                                       leek.data[field]))
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

    def stats(options):
        print('Deprecated: use "pool stats"')
        mode = options[0]
        if mode == 'infos':
            fields = {'talent': [], 'level': []}
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
        for farmer in Farmers.get():
            try:
                leek = farmer.getLeek(farmer.getFirstLeekId())
                for field in fields:
                    fields[field].append(leek.data[field])
            except ValueError as err:
                print(format(err))
        print('value : min, avg, max')
        for field in fields:
            print('{0} : {1}, {2}, {3}'.format(field, min(
                fields[field]), int(sum(fields[field]) / len(fields[field])),
                                               max(fields[field])))

    def setupAI(options):
        print('Deprecated: use "pool ais"')
        try:
            if not os.path.exists('ai'):
                raise ValueError('Can\'t find "ai" folder')

            ais = {}
            for fileName in os.listdir('ai'):
                if fileName.endswith('.leek'):
                    with open(os.path.join('ai', fileName), 'r') as myfile:
                        ais[fileName[:-5]] = myfile.read()

            if (ais.get('AI') is None):
                raise ValueError('Can\'t find "ai/AI.leek" file')

            for farmer in Farmers.get():
                try:
                    fais = farmer.getAis()
                    leek = farmer.getLeek(farmer.getFirstLeekId())
                    for ai in ais:
                        aid = None
                        for current in fais:
                            if current['name'] == ai:
                                aid = current['id']
                                break

                        if aid is None:
                            print('New ai "{0}" for {1}'.format(
                                ai, farmer.name))
                            aid = farmer.newAi(0, ai)['id']
                        farmer.saveAi(aid, ais[ai])
                        if ai == 'AI':
                            leek.setAi(aid)
                    leek.raiseError('OK')  #Ugly
                except ValueError as err:
                    print(format(err))
        except ValueError as err:
            print(format(err))

    def tournament(options):
        print('Deprecated: use "pool tournament"')
        for farmer in Farmers.get():
            try:
                leek = farmer.getLeek(farmer.getFirstLeekId())
                leek.tournament()
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def equipWeapon(options):
        print('Deprecated: use "pool equip weapon"')
        template = options[0]
        for farmer in Farmers.get():
            try:
                wid = None
                for weapon in farmer.weapons:
                    if (weapon['template'] == template):
                        wid = weapon['id']

                if wid is None:
                    farmer.raiseError(
                        'Have any {0} available'.format(template))

                leek = farmer.getLeek(farmer.getFirstLeekId())
                leek.equipWeapon(wid)
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def unequipWeapon(options):
        print('Deprecated: use "pool unequip weapon"')
        template = options[0]
        for farmer in Farmers.get():
            try:
                wid = None
                leek = farmer.getLeek(farmer.getFirstLeekId())
                for weapon in leek.weapons:
                    if (weapon['template'] == template):
                        wid = weapon['id']

                if wid is None:
                    farmer.raiseError(
                        'Have any {0} available'.format(template))

                leek.unequipWeapon(wid)
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def equipChip(options):
        print('Deprecated: use "pool equip chip"')
        template = options[0]
        for farmer in Farmers.get():
            try:
                wid = None
                for chip in farmer.chips:
                    if (chip['template'] == template):
                        wid = chip['id']

                if wid is None:
                    farmer.raiseError(
                        'Have any {0} available'.format(template))

                leek = farmer.getLeek(farmer.getFirstLeekId())
                leek.equipChip(wid)
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def unequipChip(options):
        print('Deprecated: use "pool unequip chip"')
        template = options[0]
        for farmer in Farmers.get():
            try:
                wid = None
                leek = farmer.getLeek(farmer.getFirstLeekId())
                for chip in leek.chips:
                    if (chip['template'] == template):
                        wid = chip['id']

                if wid is None:
                    farmer.raiseError(
                        'Have any {0} available'.format(template))

                leek.unequipChip(wid)
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))

    def characteristics(options):
        print('Deprecated: use "pool characteristics"')
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
        bonuses[options[1]] = options[0]
        for farmer in Farmers.get():
            try:
                leek = farmer.getLeek(farmer.getFirstLeekId())
                leek.characteristics(bonuses)
                leek.raiseError('OK')  #Ugly
            except ValueError as err:
                print(format(err))


class Farmer:
    def __init__(self, data):
        self.data = data['farmer']
        self.token = data['token']

        self.id = self.data['id']
        self.name = self.data['name']
        self.weapons = self.data['weapons']
        self.chips = self.data['chips']
        self.leeks = self.data['leeks']
        self.fights = self.data['fights']

    def raiseError(self, error):
        raise ValueError('Farmer {0} : {1}'.format(self.name, error))

    def checkRequest(self, req):
        if not req.get('success', False):
            self.raiseError(req.get('error', 'Fail'))
        return req

    def buy(self, item):
        self.checkRequest(lwapi.market.buy_habs(item, self.token))

    def sell(self, item):
        self.checkRequest(lwapi.market.sell_habs(item, self.token))

    def getLeek(self, leek):
        return Leek(
            self.checkRequest(lwapi.leek.get_private(leek, self.token)),
            self.token)

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
        self.checkRequest(lwapi.ai.save(ai, script, self.token))

    def getFirstLeekId(self):
        #NOTE: Deprecated
        return next(iter(self.leeks))


class Leek:
    def __init__(self, data, token):
        self.data = data['leek']
        self.token = token

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
            lwapi.garden.get_leek_opponents(self.id, self.token))['opponents']

    def fight(self, target):
        return self.checkRequest(
            lwapi.garden.start_solo_fight(self.id, target,
                                          self.token))['fight']

    def setAi(self, ai):
        self.checkRequest(lwapi.leek.set_ai(self.id, ai, self.token))

    def tournament(self):
        self.checkRequest(lwapi.leek.register_tournament(self.id, self.token))

    def equipWeapon(self, wid):
        self.checkRequest(lwapi.leek.add_weapon(self.id, wid, self.token))

    def unequipWeapon(self, wid):
        self.checkRequest(lwapi.leek.remove_weapon(wid, self.token))

    def equipChip(self, wid):
        self.checkRequest(lwapi.leek.add_chip(self.id, wid, self.token))

    def unequipChip(self, wid):
        self.checkRequest(lwapi.leek.remove_chip(wid, self.token))

    def characteristics(self, bonuses):
        self.checkRequest(
            lwapi.leek.spend_capital(self.id, json.dumps(bonuses), self.token))

# Main Program
if __name__ == "__main__":
    print("TODO pools, teams and so more")
    CommandTree()\
    .addCommand('farmers list', 'list all farmers', Farmers.list, [{'name': 'mode', 'optional': True, 'list': [None, 'infos', 'ais', 'stuff', 'leeks']}])\
    .addCommand('farmers stats', 'stats of all farmers', Farmers.stats, [{'name': 'mode', 'list': ['infos']}])\
    .addCommand('farmer register', 'add a new farmer',Farmers.register, [{'name': 'login'},{'name': 'password'}])\
    .addCommand('farmers buy', 'buy an item',Farmers.buy, [{'name': 'item', 'type': int}])\
    .addCommand('farmers sell', 'sell an item',Farmers.sell, [{'name': 'item', 'type': int}])\
    .addCommand('firsts fight', 'Deprecated: run solo fights for first leek of each farmer', FirstLeeks.fight, [{'name': 'count', 'optional': True, 'type': int, 'min': 1, 'max': 100}, {'name': 'force', 'optional': True, 'list': [None, 'force']}])\
    .addCommand('firsts list', 'Deprecated: list first leek of each farmer', FirstLeeks.list, [{'name': 'mode', 'optional': True, 'list': [None, 'infos', 'stuff', 'characteristics']}])\
    .addCommand('firsts stats', 'Deprecated: stats of first leek of each farmer', FirstLeeks.stats, [{'name': 'mode', 'list': ['infos', 'characteristics']}])\
    .addCommand('firsts ais', 'Deprecated: import ai/<name>.leek files and load ai/AI.leek for first leek of each farmer', FirstLeeks.setupAI, [])\
    .addCommand('firsts tournament', 'Deprecated: register first leek of each farmer for solo tournament', FirstLeeks.tournament, [])\
    .addCommand('firsts equip weapon', 'Deprecated: equip a weapon for first leek of each farmer', FirstLeeks.equipWeapon, [{'name': 'item', 'type': int}])\
    .addCommand('firsts unequip weapon', 'Deprecated: unequip a weapon for first leek of each farmer', FirstLeeks.unequipWeapon, [{'name': 'item', 'type': int}])\
    .addCommand('firsts equip chip', 'Deprecated: equip a chip for first leek of each farmer', FirstLeeks.equipChip, [{'name': 'item', 'type': int}])\
    .addCommand('firsts unequip chip', 'Deprecated: unequip a chip for first leek of each farmer', FirstLeeks.unequipChip, [{'name': 'item', 'type': int}])\
    .addCommand('firsts characteristics', 'Deprecated: buy characteristics for first leek of each farmer', FirstLeeks.characteristics, [{'name': 'count', 'type': int}, {'name': 'type', 'list': ['life', 'strength', 'wisdom', 'agility', 'resistance', 'science', 'magic', 'tp', 'mp', 'frequency']}])\
    .parse(sys.argv)