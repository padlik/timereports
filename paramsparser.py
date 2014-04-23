#!/usr/bin/env python

import ConfigParser
import argparse
import collections


CONFIG = {
    "config": (
        ('-c', '--config'),
        {'required': True, 'help': "Credentials file"}
    ),
    "year": (
        ('-y', '--year'),
        {'type': int, 'default': '2014', 'help': "Year of the report"}
    ),
    "month": (
        ('-m', '--month'),
        {'type': int, 'default': '03', 'help': "Month of the report"}
    ),
    "debug": (
        ('-d', '--debug'),
        {'help': "Turn on debug output", 'action': 'store_true'}
    )
}


class ConfigException(Exception):
    pass


class BasicParamsParser(collections.MutableMapping):
    def __init__(self, caption=None, config=None, need_help=True):
        self._args_parser = argparse.ArgumentParser(prog=caption or "program", add_help=need_help)
        self._raw_config = config or CONFIG
        self._opts = {}
        for k, v in self._raw_config.iteritems():
            self._opts[k] = None
            self._args_parser.add_argument(*v[0], **v[1])

    def parse(self, argv):
        return self._opts.update(self._args_parser.parse_args(argv).__dict__)

    def help(self):
        self._args_parser.print_help()

    @property
    def options(self):
        return self._opts

    def __getitem__(self, item):
        return self._opts[item]

    def __iter__(self):
        for k in self._opts.keys():
            yield k

    def __delitem__(self, _):
        raise ConfigException("Config item cannot be changed this way, please parse again")

    def __len__(self):
        return len(self._opts)

    def __setitem__(self, _, __):
        raise ConfigException("Config item cannot be changed this way, please parse again")


class AppParamsParser(BasicParamsParser):
    def parse(self, argv):
        args = self._args_parser.parse_args(argv)

        self._opts.update(args.__dict__)
        cp = ConfigParser.SafeConfigParser()
        if not cp.read(self._opts['config']):
            raise ConfigException("File {} not found ".format(self._opts['config']))
        for section in cp.sections():
            for k, v in self._section_map(cp, section).iteritems():
                self._opts[section + '.' + k] = v

        return self._opts

    @staticmethod
    def _section_map(parser, section):
        sm = {}
        for opt in parser.options(section):
            try:
                sm[opt] = parser.get(section, opt)
                if sm[opt] == - 1:
                    pass
            except:
                # it's filthy...
                sm[opt] = None
        return sm

