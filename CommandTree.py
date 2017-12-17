#Sheychen 2017
#CC BY
import itertools


class CommandTree:
    def __init__(self):
        self.commands = {}
        self.options = {}

    def addCommand(self, path, text, func, params):
        if self.commands.get(path) is None:
            self.commands[path] = {
                'text': text,
                'func': func,
                'params': params
            }
        else:
            print('Command {0}: Allready added'.format(path))
        return self

    def checkOption(data, param, path):
        if not param is None:
            name = param.get('name', '')
            if len(name) > 0:
                name += ':'
            if data is None:
                if not param.get('optional', False):
                    print('Wrong params count in "{0}", {1} isn\'t optional.'.
                          format(path, name))
                    return False
                else:
                    pdef = param.get('default')
                    if not pdef is None:
                        data = pdef
            else:
                ptype = param.get('type')
                if type(ptype) is type:
                    try:
                        data = ptype(data)
                    except (TypeError, ValueError) as e:
                        print('Wrong type in "{0}", {1}"{2}" must be an {3}.'.
                              format(path, name, data, ptype.__name__))
                        return False
                    if ptype == int:
                        pmin = param.get('min')
                        if type(pmin) is int:
                            if data < pmin:
                                print(
                                    'Wrong value in "{0}", {1}"{2}" must be >= {3}.'.
                                    format(path, name, data, pmin))
                                return False
                        pmax = param.get('max')
                        if type(pmax) is int:
                            if data > pmax:
                                print(
                                    'Wrong value in "{0}", {1}"{2}" must be <= {3}.'.
                                    format(path, name, data, pmax))
                                return False
                plist = param.get('list')
                if type(plist) is list:
                    if not data in plist:
                        print(
                            'Wrong value in "{0}", {1}"{2}" must be one of ({3}).'.
                            format(path, name, data, ', '.join(
                                str(x) for x in plist)))
                        return False
        else:
            print('"{0}" only accepts {1} params.'.format(
                path, len(command['params'])))
            return False
        return data

    def runCommand(self, path, args, options):
        command = self.commands[path]
        params = []
        for data, param in itertools.zip_longest(args[len(path.split()):], command['params']):
            data = CommandTree.checkOption(data, param, path)
            if data is False:
                return
            params.append(data)
        command['func'](params, options)

    def helpCommand(self, command, args, options):
        print('TODO print params details')
        print('{0}: {1}'.format(command, self.commands[command]['text']))

    def listCommands(self, paths):
        print(
            'See "help <command>" for more details or "help <command path>" to filter commands'
        )
        paths.sort()
        last = []
        for path in paths:
            current = path.split()
            for i in range(0, min(len(last), len(current))):
                if current[i] == last[i]:
                    current[i] = ' ' * len(current[i])
            last = path.split()
            print('{0}: {1}'.format(
                ' '.join(current), self.commands[path]['text'].split('\n')[0]))

    def parse(self, args):
        path = args
        name = path.pop(0)
        options = {}
        if len(path) > 0:
            while path[0].startswith('-'):
                option = path.pop(0)[1:]
                for key in self.options:
                    if option in self.options[key]['names']:
                        data = CommandTree.checkOption(
                            path.pop(0), self.options[key]['check'], option)
                        if data is False:
                            return
                        options[key] = data
                        option = None
                if not option is None:
                    print('Unknown option "{0}"'.format(option))
                    return
        for key in self.options:
            data = CommandTree.checkOption(
                options.get(key), self.options[key]['check'], key)
            if data is False:
                return
            options[key] = data
        commands = list(self.commands.keys())
        if len(path) > 0:
            run = self.runCommand
            if path[0] == 'help':
                path.pop(0)
                run = self.helpCommand

            for i in range(0, len(path)):
                newcommands = []
                for command in commands:
                    splits = command.split()
                    if len(splits) >= i:
                        if splits[i] == path[i]:
                            newcommands.append(command)
                commands = newcommands
                if len(commands) <= 1:
                    break

            if len(commands) == 0:
                print('Unknown command "{0}"'.format(' '.join(path)))
                print('See "{0} help"'.format(name))
            elif len(commands) == 1:
                run(commands[0], args, options)
            else:
                self.listCommands(commands)
        else:
            self.listCommands(commands)

    def addOption(self, key, names, check):
        if self.options.get(key) is None:
            self.options[key] = {'names': names, 'check': check}
        else:
            print('Option {0}: Allready added'.format(key))
        return self