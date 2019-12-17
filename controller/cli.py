# Copyright 2018-present University of Tuebingen, Chair of Communication Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Marco Haeberle (marco.haeberle@uni-tuebingen.de)
#
#

import cmd
import datetime


class CLI(cmd.Cmd):
    def set_topo(self, topo):
        self.topo = topo

    def set_control_client(self, control_client):
        self.control_client = control_client

    def do_EOF(self, line):
        return True

    def do_show_topo(self, line):
        "show the topology"
        print(self.topo)

    def do_exit(self, line):
        return True

    def do_add_example_MACsec_rules(self, line):
        self.control_client.addMACsecProtectRule('s1', 2, '62:88:00:00:00:02', '00112233445566778899AABBCCDDEE21')
        self.control_client.addMACsecProtectRule('s2', 2, '62:88:00:00:00:01', '11111111111111111111111111111111')
        self.control_client.addMACsecValidateRule('s1', 2, '11111111111111111111111111111111')
        self.control_client.addMACsecValidateRule('s2', 2, '00112233445566778899AABBCCDDEE21')
