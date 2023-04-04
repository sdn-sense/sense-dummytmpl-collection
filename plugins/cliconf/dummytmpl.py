#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import json

from ansible.module_utils._text import to_text
from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list

class Cliconf(CliconfBase):

    def get_device_info(self):
        """Get Device Info"""
        devInfo = {}

        devInfo['network_os'] = 'sense.dummytmpl.dummytmpl'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        devInfo['debug'] = data
        # MUST RETURN Dictionary, with values for these keys:
        # network_os, os_version, os_hwid, os_hostname
        return devInfo

    @enable_mode
    def get_config(self, source='running', flags=None, format='text'):
        """Get Config"""
        if source not in ['running', 'startup']:
            return self.invalid_params(f"fetching configuration from {source} is not supported")
        if source == 'running':
            cmd = 'show running-config all'
        else:
            cmd = 'show startup-config'
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        """Edit Configuration"""
        for cmd in ['configure terminal'] + to_list(command) + ['end']:
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        """Get command output"""
        return self.send_command(command=command, prompt=prompt, answer=answer,
                                 sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        """Get capabilities"""
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
