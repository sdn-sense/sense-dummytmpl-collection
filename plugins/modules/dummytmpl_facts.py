#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.utils.display import Display
from ansible_collections.sense.dummytmpl.plugins.module_utils.network.dummytmpl import run_commands
from ansible_collections.sense.dummytmpl.plugins.module_utils.network.dummytmpl import dummytmpl_argument_spec, check_args

display = Display()

class FactsBase():
    """Base class for Facts"""

    COMMANDS = {}

    def __init__(self, module):
        self.module = module
        self.facts = {}
        self.rawout = {}
        self.responses = None

    def populate(self):
        """Populate responses"""
        self.responses = run_commands(self.module, self.COMMANDS.values(), check_rc=False)

    def run(self, cmd):
        """Run commands"""
        return run_commands(self.module, cmd, check_rc=False)

    def save_raw(self, commands):
        """Save RAW Output for debugging"""
        counter = 0
        for key, _cmd in commands.items():
            self.rawout.setdefault(f'{key}_raw', {})
            try:
                self.rawout[f'{key}_raw'] = self.responses[counter]
            except IndexError:
                pass
            counter +=1


class Default(FactsBase):
    """Default Class to get basic info"""
    COMMANDS = {'version': 'show version',
                'system': 'show system'}

    def populate(self):
        super(Default, self).populate()
        self.save_raw(self.COMMANDS)
        # set facts version, hwid, hostname


class Hardware(FactsBase):
    """Hardware Information Class"""
    COMMANDS = {'version': 'show version',
               'memory': 'show processes node-id 1 | grep "Mem :"'}

    def populate(self):
        super(Hardware, self).populate()
        # set memfree, memtotal,memused (in mb)
        self.save_raw(self.COMMANDS)


class Config(FactsBase):
    """Configuration info Class"""
    COMMANDS = {'running-config': 'show running-config'}

    def populate(self):
        super(Config, self).populate()
        self.save_raw(self.COMMANDS)
        # Set raw running config


class Interfaces(FactsBase):
    """All Interfaces Class"""
    COMMANDS = {'interfaces': 'show interface',
                'interfaces-brief': 'show ip interface brief',
                'interfaces-ipv6': 'show ipv6 interface brief',
                'lldp-neighbors': 'show lldp neighbors detail'}

    def populate(self):
        super(Interfaces, self).populate()
        self.save_raw(self.COMMANDS)

class Routing(FactsBase):
    """Routing Information Class"""
    COMMANDS = {'ip-route': 'show ip route',
                'ipv6-route': 'show ipv6 route'}

    def populate(self):
        super(Routing, self).populate()
        self.save_raw(self.COMMANDS)

FACT_SUBSETS = {'default': Default,
                'hardware': Hardware,
                'interfaces': Interfaces,
                'routing': Routing,
                'config': Config}

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = {'gather_subset': {'default': ['!config'], 'type': 'list'}}
    argument_spec.update(dummytmpl_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    gather_subset = module.params['gather_subset']
    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue
        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False
        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset')
        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)
    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = {}
    facts['gather_subset'] = [runable_subsets]

    instances = []
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = {}
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    warnings = []
    check_args(module, warnings)
    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
