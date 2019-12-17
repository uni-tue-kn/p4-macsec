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
# Joshua Hartmann
#
#

import cmd
import datetime

import struct
from scapy.all import Packet, Ether
from scapy.contrib import lldp

class CLI(cmd.Cmd):
    def set_controller(self, controller):
        print('set controller')
        self.controller = controller

    def do_EOF(self, line):
        return True

    def do_connections(self, line):
        "connections - Lists the currently recognized connections"

        for index, conn in enumerate(self.controller.connection_info):
            print(
                "connection {4}: Port {1} of switch {0} is connected to port {3} of switch {2} [macsec_enabled: {5}]".format(
                    conn['sw_name_1'], conn['sw_port_1'],
                    conn['sw_name_2'], conn['sw_port_2'],
                    index, conn['macsec_enabled']))
        if len(self.controller.connection_info) == 0:
            print("no connections recognized yet")

    def do_list_switches(self, line):
        "list_switches - Lists the currently connected switches"
        for sw in self.controller.switches:
            print(sw)

    def do_set_port_addr(self, line):
        (switch_name, port, addr) = line.split(" ")

        self.controller.writeOutPortToAddrRules(sw=self.controller.name2switch[switch_name],
                                                addr=addr,
                                                port=int(port));

        self.controller.writeInPortToAddrRules(sw=self.controller.name2switch[switch_name],
                                               addr=addr,
                                               port=int(port));

    def do_read_table_rules(self, line):
        try:
            sw = self.controller.name2switch[line]
        except KeyError:
            print('illegal arguments: "' + line + '"')
            return
        print("reading table rules of {0}".format(sw))

        self.controller.read_table_rules(sw)

    def complete_read_table_rules(self, text, line, begidx, endidx):
        if not text:
            return [sw.name for sw in self.controller.switches]
        else:
            return [sw.name for sw in self.controller.switches if sw.name.startswith(text)]

    def do_show_l2_mappings(self, line):
        [s0] = self.controller.switches

        print('MAC\t\t\t| Port')
        print('-------------------------------')
        for mac in self.controller.l2_mapping[s0.name]:
            print(mac + "\t| " + str(self.controller.l2_mapping[s0.name][mac]))

    def do_write_default_ipv4_lpm_rules_1(self, line):
        [s0] = self.controller.switches

        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.1.1", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:01:01", port=1)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.2.2", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:02:02", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.2.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:02:02", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.3.3", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:03:03", port=3)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.3.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:03:03", port=3)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_default_ipv4_lpm_rules_2(self, line):
        [s0] = self.controller.switches

        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.1.1", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:01:01", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.1.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:01:01", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.2.2", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:02:02", port=1)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.3.3", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:03:03", port=3)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.3.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:03:03", port=3)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_default_ipv4_lpm_rules_3(self, line):
        [s0] = self.controller.switches

        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.1.1", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:01:01", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.1.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:01:01", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.2.2", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:02:02", port=3)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.2.254", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:02:02", port=2)
        self.controller.writeIPv4LPMRules(sw=s0, ip_addr="10.0.3.3", ip_prefix=32,
                                          dst_eth_addr="00:00:00:00:03:03", port=1)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_default_l2_mapping_1(self, line):
        [s0] = self.controller.switches

        self.controller.updateL2Entry(s0, "00:00:00:00:01:01", 1)
        self.controller.updateL2Entry(s0, "00:00:00:00:02:02", 2)
        self.controller.updateL2Entry(s0, "00:00:00:00:03:03", 3)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_default_l2_mapping_2(self, line):
        [s0] = self.controller.switches

        self.controller.updateL2Entry(s0, "00:00:00:00:01:01", 2)
        self.controller.updateL2Entry(s0, "00:00:00:00:02:02", 1)
        self.controller.updateL2Entry(s0, "00:00:00:00:03:03", 3)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_default_l2_mapping_3(self, line):
        [s0] = self.controller.switches

        self.controller.updateL2Entry(s0, "00:00:00:00:01:01", 2)
        self.controller.updateL2Entry(s0, "00:00:00:00:02:02", 3)
        self.controller.updateL2Entry(s0, "00:00:00:00:03:03", 1)

        print "Installed ipv4_lpm rules on %s" % s0.name

    def do_write_example_MACsec_rules_1(self, line):
        [s0] = self.controller.switches

        self.controller.writeMACsecRulesProtect(sw=s0, port=2, key='00112233445566778899AABBCCDDEE21', system_id = '00:00:00:00:01:01')
        self.controller.writeMACsecRulesValidate(sw=s0, port=2, key='11111111111111111111111111111111')

        print "Installed MACsec rules on %s" % s0.name

    def do_write_example_MACsec_rules_2(self, line):
        [s0] = self.controller.switches

        self.controller.writeMACsecRulesProtect(sw=s0, port=2, key='11111111111111111111111111111111', system_id = '00:00:00:00:02:02')
        self.controller.writeMACsecRulesValidate(sw=s0, port=2, key='00112233445566778899AABBCCDDEE21')

        print "Installed MACsec rules on %s" % s0.name

    def do_send_lldp_packet(self, line):
        [s0] = self.controller.switches
        port = int(line)

        pkt =  Ether(src='00:00:00:00:00:00', dst='ff:ff:ff:ff:ff:ff')
        lldp_chassis_id = lldp.LLDPDUChassisID(id=str.encode(s0.name))
        lldp_port_id = lldp.LLDPDUPortID(id=struct.pack(">H", port))
        lldp_timte_to_live = lldp.LLDPDUTimeToLive(ttl=6)
        lldp_end_of_lldp = lldp.LLDPDUEndOfLLDPDU()

        pkt = pkt / lldp_chassis_id / lldp_port_id / lldp_timte_to_live / lldp_end_of_lldp
        #cpu header: q hat Laenge 8, w hat Laenge 2
        reason = struct.pack(">H", 4)
        out_port = struct.pack(">H", port)
        zeros = struct.pack(">q", 0)
        cpu_header = zeros + reason + out_port

        self.controller.send_packet_out(s0, cpu_header + str(pkt))


    def do_exit(self, line):
        return True
