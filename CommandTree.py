#Sheychen 2017
#CC BY
import itertools


class CommandTree:
    def __init__(self):
        self.commands = {}
        #self.options = {}

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

    def runCommand(self, path, args):
        command = self.commands[path]
        params = []
        for data, param in itertools.zip_longest(args[len(path.split()):], command['params']):
            if not param is None:
                name = param.get('name', '')
                if len(name) > 0:
                    name += ':'
                if data is None:
                    if not param.get('optional', False):
                        print('Wrong params count in "{0}", {1} isn\'t optional.'.
                            format(path, name))
                        return
                else:
                    ptype = param.get('type')
                    if type(ptype) is type:
                        try:
                            data = ptype(data)
                        except (TypeError, ValueError) as e:
                            print('Wrong type in "{0}", {1}"{2}" must be an {3}.'.format(
                                path, name, data, ptype.__name__))
                            return
                        if ptype == int:
                            pmin = param.get('min')
                            if type(pmin) is int:
                                if data < pmin:
                                    print('Wrong value in "{0}", {1}"{2}" must be >= {3}.'.
                                        format(path, name, data, pmin))
                                    return
                            pmax = param.get('max')
                            if type(pmax) is int:
                                if data > pmax:
                                    print('Wrong value in "{0}", {1}"{2}" must be <= {3}.'.
                                        format(path, name, data, pmax))
                                    return
                    plist = param.get('list')
                    if type(plist) is list:
                        if not data in plist:
                            print(
                                'Wrong value in "{0}", {1}"{2}" must be one of ({3}).'.
                                format(path, name, data, ', '.join(
                                    str(x) for x in plist)))
                            return
            else:
                print('"{0}" only accepts {1} params.'.format(
                    path, len(command['params'])))
                return

            params.append(data)
        command['func'](params)

    def helpCommand(self, command, args):
        print('TODO print params details')
        print('{0}: {1}'.format(command, self.commands[command]['text']))

    def listCommands(self, paths):
        print('TODO print short params')
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
        #TODO parse options
        path = args
        name = path.pop(0)
        commands = list(self.commands.keys())
        if len(args) > 0:
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
                run(commands[0], args)
            else:
                self.listCommands(commands)
        else:
            self.listCommands(commands)

    '''
    def addOption(self, key, names, options):
        if self.options.get(key) is None:
            self.options[key] = {'names': names, 'options': options}
        else:
            print('Option {0}: Allready added'.format(key))
        return self

    def getOption(self, key):
        option = self.options.get(key)
        if not option is dict:
            return option.get('value')
        else:
            return option
    '''
