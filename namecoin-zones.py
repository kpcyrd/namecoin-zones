#!/usr/bin/env python
from argparse import ArgumentParser
from jsonrpclib import Server
from time import time
import socket
import json
import yaml
import re


class Rpc(object):
    def __init__(self, config):
        self.rpc = Server(config)

    def get_blocks(self):
        return self.rpc.getinfo()['blocks']

    def get_names_as_dict(self):
        return self.rpc.name_filter('^d/[a-z0-9_-]+$', 0)

    def get_names(self):
        return [Name(x) for x in self.get_names_as_dict()]


class Name(object):
    def __init__(self, name):
        self.name = name['name']
        self.expired = 'expired' in name
        self.json = None

        if not self.expired:
            self.expires_in = name['expires_in']
            self.value = name['value']
            try:
                self.json = json.loads(self.value)
            except ValueError:
                pass


def ensure_is_list(x):
    return x if type(x) is list else [x]


def is_valid_ip(x):
    try:
        socket.inet_pton(socket.AF_INET, x)
        return True
    except:
        return False


def is_valid_ip6(x):
    try:
        socket.inet_pton(socket.AF_INET6, x)
        return True
    except:
        return False


def is_valid_name(x):
    return re.match('^([a-zA-Z0-9._-]+\.)*[a-zA-Z0-9._-]+\.?$', x)


class Entry(object):
    def __init__(self, name, entries):
        self.domain = name[2:]

        self.a = []
        self.aaaa = []
        self.ns = []
        self.cname = []

        self.process_map(self.domain, entries)

    def process_map(self, domain, entries):
        try:
            for x, y in entries.items():
                if x == 'ip':
                    self.add_a(domain, y)
                elif x == 'ip6':
                    self.add_aaaa(domain, y)
                elif x == 'map':
                    for a, b in y.items():
                        sub = a
                        if sub:
                            sub += '.'
                        self.process_map(sub + domain, b)
                elif x == 'ns':
                    self.add_ns(domain, y)
                elif x == 'translate':
                    self.add_cname(domain, y)
        except AttributeError:
            pass

    def add_a(self, domain, entries):
        for z in ensure_is_list(entries):
            if is_valid_ip(z):
                self.a.append((domain, z))

    def add_aaaa(self, domain, entries):
        for z in ensure_is_list(entries):
            if is_valid_ip6(z):
                self.aaaa.append((domain, z))

    def add_ns(self, domain, entries):
        for z in ensure_is_list(entries):
            if is_valid_name(z):
                if z[-1] != '.':
                    z += '.'
                self.ns.append((domain, z))

    def add_cname(self, domain, entries):
        for z in ensure_is_list(entries):
            if is_valid_name(z):
                if z[-1] != '.':
                    z += '.'
                self.cname.append((domain, z))


def names_to_bind(names, config):
    with open('zone-template.conf') as f:
        for x in f:
            x = x.replace('@@DOMAIN@@', config['suffix'])
            x = x.replace('%%serial%%', '%d' % (time() - 1415194620))
            x = x.replace('%%authns%%', config['authNS'])
            x = x.replace('%%email%%', 'hostmaster.' + config['authNS'])
            yield x.rstrip()

    for name in names:
        if name.json:
            entry = Entry(name.name, name.json)
            for x, y in entry.a:
                yield '%-40s IN\tA\t%s' % (x, y)
            for x, y in entry.aaaa:
                yield '%-40s IN\tAAAA\t%s' % (x, y)
            for x, y in entry.ns:
                yield '%-40s IN\tNS\t%s' % (x, y)
            for x, y in entry.cname:
                yield '%-40s IN\tCNAME\t%s' % (x, y)


def load_config(path):
    with open(path) as f:
        return yaml.load(f)


def main():
    args = parser.parse_args()

    config = load_config(args.config)
    rpc = Rpc(config['server'])

    names = rpc.get_names()

    for line in names_to_bind(names, config):
        print(line)


parser = ArgumentParser()
parser.add_argument('config')

if __name__ == '__main__':
    main()
