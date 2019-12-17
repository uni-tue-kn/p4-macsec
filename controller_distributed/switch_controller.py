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

import p4runtime_lib.bmv2
import p4runtime_lib.helper

import port
import os

import threading
import Queue
import struct

import binascii

from time import sleep, time
#
# from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet, Ether, ARP, hexdump
#from scapy.layers.inet import IP, UDP, TCP
from scapy.contrib import lldp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

class SwitchController:
    def __init__(self, p4info_file_path, bmv2_file_path=None, topo_client=None, mac_address=None):
        self.switches = []
        self.name2switch = {}
        self.port_queues = {}
        self.port_threads = {}
        self.connection_info = []
        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
        self.p4info_file_path = p4info_file_path
        self.bmv2_file_path = bmv2_file_path
        self.packet_in_threads = []
        self.topo = {}
        self.topo_lock = threading.Lock()
        self.topo_client = topo_client
        self.bddp_seq = int(time())
        self.bddp_recv_seq = {}
        self.mac_address = mac_address
        self.register_pn_outgoing = [None]*64
        self.l2_mapping = {}
        self.l2_mapping_lock = threading.Lock()
        self.l2_mapping_timeout = 30 #s
        self.lldp_interval = 30 #s
        self.num_ports = {}

    def add_switch_connection(self, name, address, device_id, type = 'bmv2',
                              crypto_address = None, debug=False, notification_socket = None,
                              num_ports = 15):
        if type == 'bmv2':
            sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=name,
                    address=address, device_id=device_id, debug=debug)

            self.port_queues[sw.name] = Queue.Queue()

            port_monitor = port.PortMonitor(self.port_queues[sw.name], notification_socket)
            self.port_threads[sw.name] = threading.Thread(target=port_monitor.monitor_messages)
            self.port_threads[sw.name].daemon = True
            self.port_threads[sw.name].start()

            port_t = threading.Thread(target=self.check_port_queue, args=(name,))
            port_t.daemon = True
            port_t.start()

            lldp_periodic_t = threading.Thread(target=self.periodic_lldp, args=(name,num_ports))
            lldp_periodic_t.daemon = True
            lldp_periodic_t.start()

        elif type == 'tofino':
            sw = p4runtime_lib.switch.SwitchConnection(name=name, address=address,
                    device_id=device_id, type='tofino',  crypto_address = crypto_address,
                    debug=debug)

        self.switches.append(sw)
        self.name2switch[sw.name] = sw
        self.topo_lock.acquire()
        self.topo[sw.name] = {}
        self.topo_lock.release()
        self.l2_mapping[sw.name] = {}
        self.num_ports[sw.name] = num_ports

        l2_periodic_t = threading.Thread(target=self.periodic_l2_timeout_check, args=(sw,))
        l2_periodic_t.daemon = True
        l2_periodic_t.start()


    def startup(self):
        for sw in self.switches:
            sw.SetForwardingPipelineConfig(p4info=self.p4info_helper.p4info,
                                           bmv2_json_file_path=self.bmv2_file_path)
            t = threading.Thread(target=sw.send_init_and_wait, args=(self.response_callback, ))
            t.start()
            self.packet_in_threads.append(t)

    def teardown(self):
        for sw in self.switches:
            sw.stop_waiting()
        for t in self.packet_in_threads:
            t.join()

    def send_packet_out(self, switch, payload):
        switch.send_packet_out(payload)

    def send_packet_out_multiple(self, switch, payloads):
        switch.send_packet_out_multiple(payloads)

    def response_callback(self, switch, response):
        #print("got a response from switch %s" % switch.name)
        if response.packet.payload:
            self.packet_in_callback(switch, response.packet.payload)
        else:
            #print("Non packet_in response: \n"  + str(response))
            pass

    def packet_in_callback(self, switch, packet_in):
        # remove CPU header
        reason = struct.unpack(">H", packet_in[8:10])[0]
        ingress_port = struct.unpack(">H", packet_in[10:12])[0]
        timestamp = int(str(binascii.hexlify(packet_in[12:18])), 16)
        print("Packet in, reason: " + str(reason) + ", in port: " + str(ingress_port) + ", timestamp: " + str(timestamp))
        pkt = Ether(packet_in[18:])

        # learn source mac if necessary
        self.l2_mapping_lock.acquire()
        if pkt[Ether].src not in self.l2_mapping[switch.name] or self.l2_mapping[switch.name][pkt[Ether].src]['port'] == 0x1FF:
            self.l2_mapping_lock.release()
            self.updateL2Entry(switch, pkt[Ether].src, ingress_port, timestamp)
        else:
            self.l2_mapping_lock.release()



        # source mac unknown (2)
        if reason == 2:
            # already learnd source mac because of packet in, send back to switch
            print('learned src mac -> port mappping')

            self.l2_mapping_lock.acquire()
            if pkt[Ether].dst not in self.l2_mapping[switch.name]:
                # flood if dst mac unknown, otherwise packet would be sent back
                # to switch and flooded on all ports because controller is source port
                reason = 1
                self.l2_mapping_lock.release()
            else:
                self.l2_mapping_lock.release()
                self.packet_out(switch, 60002, 0, pkt)
                return

        # src mac timeout (3) or src mac changed port (4)
        if reason == 3 or reason == 4:
            # update src mac timout
            self.updateL2Entry(switch, pkt[Ether].src, ingress_port, timestamp)

            print('refresh src mac entry')
            self.l2_mapping_lock.acquire()
            if pkt[Ether].dst not in self.l2_mapping[switch.name]:
                # flood if dst mac unknown, otherwise packet would be sent back
                # to switch and flooded on all ports because controller is source port
                reason = 1
                self.l2_mapping_lock.release()
            else:
                self.l2_mapping_lock.release()
                self.packet_out(switch, 60002, 0, pkt)
                return

        # destination mac unknown (1)
        if reason == 1:
            # add preliminary entry to prevent switch from sending more packets
            if  pkt[Ether].dst != 'ff:ff:ff:ff:ff:ff':
                self.updateL2Entry(switch, pkt[Ether].dst, 0x1FF, timestamp)

            print('Destination mac unknown, flood packet')
            self.flooding(switch, pkt, ingress_port)
            return

        # flood ARP
        if  reason == 10:
            print('ARP')
            self.l2_mapping_lock.acquire()
            if pkt[Ether].dst in self.l2_mapping[switch.name]:
                self.packet_out(switch, 60001, self.l2_mapping[switch.name][pkt[Ether].dst]['port'], pkt)
            else:
                self.flooding(switch, pkt, ingress_port)
            self.l2_mapping_lock.release()
            return

        # encrypted LLDP/BDDP in
        if reason == 11 and pkt[Ether].type == 0x8999:
            if self.topo_client.key_bddp is None:
                print("ERROR: cant encrypt lldp because key is not set")
                return

            nonce = packet_in[32:44]
            seq = packet_in[44:48]
            seq_int = struct.unpack(">i", seq)[0]

            if pkt[Ether].src not in self.bddp_recv_seq or seq_int > self.bddp_recv_seq[pkt[Ether].src]:
                self.bddp_recv_seq[pkt[Ether].src] = seq_int
            else:
                print("received duplicate sequence number from " + pkt[Ether].src)
                return

            aesgcm = AESGCM(self.topo_client.key_bddp)
            try:
                plaintext = aesgcm.decrypt(nonce, packet_in[48:], seq)

                # replace ethernet payload with plaintext
                pkt[Ether].type = 0x88cc
                pkt[Ether].remove_payload()
                pkt = pkt / plaintext

                # re-interpret packet with replaced payload for further processing
                pkt = Ether(str(pkt))
                reason = 10
            except InvalidTag:
                print("ERROR: invalid tag in encrypted bddp packet")
                return

        # LLDP in or further processing of encrypted LLDP/BDDP
        if reason == 10 and pkt[Ether].type == 0x88cc:
            chassis_id = pkt[lldp.LLDPDUChassisID].id
            port_id = int(pkt[lldp.LLDPDUPortID].id.encode('hex'), 16)
            tmp_topo = {}
            tmp_topo['chassis'] = chassis_id
            tmp_topo['port'] = port_id
            tmp_topo['direct'] = True
            tmp_topo['last_seen'] = time()

            topo_change = False
            self.topo_lock.acquire()
            if (ingress_port not in self.topo[switch.name]
                or self.topo[switch.name][ingress_port]['chassis'] != chassis_id
                or self.topo[switch.name][ingress_port]['port'] != port_id
                or self.topo[switch.name][ingress_port]['direct'] != True):

                    topo_change = True

            # replace even when no change because last_seen needs to be updated
            self.topo[switch.name][ingress_port] = tmp_topo
            self.topo_lock.release()

            print('received LLDP packet')
            print('Ingress Port: ' + str(ingress_port))
            print('Chassis ID: ' + str(chassis_id))
            print('Port ID: ' + str(port_id))

            if topo_change:
                print('\ntopology changed: yes')
                self.topo_lock.acquire()
                # remove 'last_seen' items from topology
                topo_filtered = {k: {k2:v2 for (k2,v2) in filter(lambda (x,y):x != 'last_seen', v.iteritems())} for (k,v) in self.topo[switch.name].iteritems()}
                self.topo_client.updateTopo(switch.name, topo_filtered)
                self.topo_lock.release()
            else:
                print('\ntopology changed: no')

            print('\nfull Topology:')
            print(self.topo[switch.name])
            print('---')
            return

        print('reason unknown or wrong ethertype')

    def assemble_packet(self, reason, port, pkt):
        reason_h = struct.pack(">H", reason)
        out_port_h = struct.pack(">H", port)
        zeros_h = struct.pack(">q", 0)
        timestamp1_h = struct.pack('<H', 0)
        timestamp2_h = struct.pack('<H', 0)
        timestamp3_h = struct.pack('<H', 0)
        cpu_header = zeros_h + reason_h + out_port_h + timestamp1_h + timestamp2_h + timestamp3_h

        return cpu_header + str(pkt)

    def packet_out(self, switch, reason, port, pkt):
        self.send_packet_out(switch, self.assemble_packet(reason, port, pkt))

    def flooding(self, switch, pkt, exclude_port):
        pkts = []
        for i in range(1, int(self.num_ports[switch.name])):
            if i != exclude_port:
                print('flooding, port ' + str(i))
                pkts.append(self.assemble_packet(60001, i, pkt))

        self.send_packet_out_multiple(switch, pkts)
        return

    def read_table_rules(self, sw):
        '''
        Reads the table entries from all tables on the switch.

        :param sw: the switch connection
        '''
        print '\n----- Reading tables rules for %s -----' % sw.name
        for response in sw.ReadTableEntries():
            for entity in response.entities:
                entry = entity.table_entry
                table_name = self.p4info_helper.get_tables_name(entry.table_id)
                print '%s: ' % table_name,
                for m in entry.match:
                    print self.p4info_helper.get_match_field_name(table_name, m.field_id),
                    print '%r' % (self.p4info_helper.get_match_field_value(m),),
                action = entry.action.action
                action_name = self.p4info_helper.get_actions_name(action.action_id)
                print '->', action_name,
                for p in action.params:
                    print self.p4info_helper.get_action_param_name(action_name, p.param_id),
                    print '%r' % p.value,
                print

    def writeMACsecRulesProtect(self, sw, port, key, system_id):
        # get register number for outgoing packet numbers
        try:
            reg_num = self.register_pn_outgoing.index(None)
        except ValueError:
            print("ERROR: can't add MACsec rule because all registers for outgoing packet numbers are in use!")
            return

        self.register_pn_outgoing[reg_num] = port

        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyEgress.protect_tbl",
            match_fields={
                "standard_metadata.egress_port": port
            },
            action_name="MyEgress.protect_packet",
            action_params={
                "key": bytes(bytearray.fromhex(key)),
                "system_id": system_id,
                "reg": reg_num
            })
        sw.WriteTableEntry(table_entry)

    def deleteMACsecRulesProtect(self, sw, port):
        # clear register number for outgoing packet numbers
        try:
            reg_num = self.register_pn_outgoing.index(port)
        except ValueError:
            print("ERROR: can't delete MACsec rule because it does not exist!")
            return

        self.register_pn_outgoing[reg_num] = None

        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyEgress.protect_tbl",
            match_fields={
                "standard_metadata.egress_port": port
            })
        sw.DeleteTableEntry(table_entry)

    def writeMACsecRulesValidate(self, sw, port, key):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.validate_tbl",
            match_fields={
                "standard_metadata.ingress_port": port
            },
            action_name="MyIngress.validate_packet",
            action_params={
                "key": bytes(bytearray.fromhex(key))
            })
        sw.WriteTableEntry(table_entry)

    def deleteMACsecRulesValidate(self, sw, port):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.validate_tbl",
            match_fields={
                "standard_metadata.ingress_port": port
            })
        sw.DeleteTableEntry(table_entry)

    def writeIPv4LPMRules(self, sw, ip_addr, ip_prefix, dst_eth_addr, port):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.ipv4_lpm",
            match_fields={
                "hdr.ipv4.dstAddr": (ip_addr, ip_prefix)
            },
            action_name="MyIngress.ipv4_forward",
            action_params={
                "dstAddr":dst_eth_addr,
                "port": port
            })
        sw.WriteTableEntry(table_entry)

    def writeL2Mapping(self, sw, mac, port, timestamp):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.mac_dst",
            match_fields={
                "hdr.ethernet.dstAddr": mac
            },
            action_name="MyIngress.l2_forward",
            action_params={
                "port": port
            })
        sw.WriteTableEntry(table_entry)

        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.mac_src",
            match_fields={
                "hdr.ethernet.srcAddr": mac
            },
            action_name="MyIngress.src_known",
            action_params={
                "port": port,
                "timestamp": timestamp
            })
        sw.WriteTableEntry(table_entry)

    def deleteL2Mapping(self, sw, mac):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.mac_dst",
            match_fields={
                "hdr.ethernet.dstAddr": mac
            })
        sw.DeleteTableEntry(table_entry)

        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.mac_src",
            match_fields={
                "hdr.ethernet.srcAddr": mac
            })
        sw.DeleteTableEntry(table_entry)

    def updateL2Entry(self, sw, mac, port, timestamp):
        self.l2_mapping_lock.acquire()
        if mac in self.l2_mapping[sw.name]:
            self.deleteL2Mapping(sw, mac)

        timeout = timestamp + int(self.l2_mapping_timeout * 10**6 * 0.6)
        self.writeL2Mapping(sw, mac, port, timeout)
        self.l2_mapping[sw.name][mac] = {}
        self.l2_mapping[sw.name][mac]['port'] = port
        self.l2_mapping[sw.name][mac]['added'] = time()
        self.l2_mapping_lock.release()
        print('updated L2 mapping: ' + mac + " -> Port " + str(port) + ", timeout: " + str(timeout))

    def deleteL2Entry(self, sw, mac):
        self.l2_mapping_lock.acquire()
        if mac not in self.l2_mapping[sw.name]:
            print('ERROR: can\'t delete L2 entry, not existing')
            self.l2_mapping_lock.release()
            return

        self.deleteL2Mapping(sw, mac)
        del self.l2_mapping[sw.name][mac]
        self.l2_mapping_lock.release()
        print('deleted L2 mapping for: ' + mac)

    def generate_lldp_packet(self, switch_name, port):
        pkt =  Ether(src=self.mac_address, dst='ff:ff:ff:ff:ff:ff')
        lldp_chassis_id = lldp.LLDPDUChassisID(id=str.encode(switch_name))
        lldp_port_id = lldp.LLDPDUPortID(id=struct.pack(">H", port))
        lldp_timte_to_live = lldp.LLDPDUTimeToLive(ttl=6)
        lldp_end_of_lldp = lldp.LLDPDUEndOfLLDPDU()

        pkt = pkt / lldp_chassis_id / lldp_port_id / lldp_timte_to_live / lldp_end_of_lldp
        #cpu header: q hat Laenge 8, w hat Laenge 2
        reason = struct.pack(">H", 60001)
        out_port = struct.pack(">H", port)
        zeros = struct.pack(">q", 0)
        timestamp1 = struct.pack('<H', 0)
        timestamp2 = struct.pack('<H', 0)
        timestamp3 = struct.pack('<H', 0)
        cpu_header = zeros + reason + out_port + timestamp1 + timestamp2 + timestamp3

        print('sending LLDP packet on port ' + str(port))
        return(cpu_header + str(pkt))

    def generate_bddp_packet(self, switch_name, port):
        if self.topo_client.key_bddp is None:
            print("ERROR: cant encrypt lldp because key is not set")
            return

        ether =  Ether(src=self.mac_address, dst='ff:ff:ff:ff:ff:ff', type=0x8999)
        lldp_chassis_id = lldp.LLDPDUChassisID(id=str.encode(switch_name))
        lldp_port_id = lldp.LLDPDUPortID(id=struct.pack(">H", port))
        lldp_timte_to_live = lldp.LLDPDUTimeToLive(ttl=6)
        lldp_end_of_lldp = lldp.LLDPDUEndOfLLDPDU()

        lldp_p = ether / lldp_chassis_id / lldp_port_id / lldp_timte_to_live / lldp_end_of_lldp
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.topo_client.key_bddp)
        seq = struct.pack(">i", self.bddp_seq)
        ciphertext = aesgcm.encrypt(nonce, str(lldp_p)[14:], seq)

        self.bddp_seq = self.bddp_seq + 1
        #cpu header: q hat Laenge 8, w hat Laenge 2
        reason = struct.pack(">H", 60001)
        out_port = struct.pack(">H", port)
        zeros = struct.pack(">q", 0)
        timestamp1 = struct.pack('<H', 0)
        timestamp2 = struct.pack('<H', 0)
        timestamp3 = struct.pack('<H', 0)
        cpu_header = zeros + reason + out_port + timestamp1 + timestamp2 + timestamp3

        print('sending BDDP packet on port ' + str(port))
        return(cpu_header + str(ether) + nonce + seq + ciphertext)

    def check_port_queue(self, switch_name):
        while True:
            status_change = self.port_queues[switch_name].get(block=True)

            # port down
            if status_change[2] == 0 and status_change[1] in self.topo[switch_name]:
                self.topo_lock.acquire()
                del self.topo[switch_name][status_change[1]]
                self.topo_client.updateTopo(switch_name, self.topo[switch_name])
                self.topo_lock.release()
                print('\nPort down, new topology:')
                print(self.topo[switch_name])
                print('---')

            # port up
            elif status_change[2] == 1:
                print('Port ' + str(status_change[2]) + ' up, sending LLDP packet')
                self.generate_bddp_packet(switch_name, status_change[1])

    def periodic_lldp(self, switch_name, port_max):
        sleep(10) # wait after startup until connection is ready

        while True:
            pkts = []
            for i in range(0, int(port_max)):
                if i in self.topo[switch_name] and self.topo[switch_name][i]['last_seen'] + 4*self.lldp_interval < time():
                    self.topo_lock.acquire()
                    del self.topo[switch_name][i]
                    self.topo_client.updateTopo(switch_name, self.topo[switch_name])
                    self.topo_lock.release()
                    print('timeoute, delete switch ' + str(switch_name) + ' port ' + str(i))

                pkts.append(self.generate_bddp_packet(switch_name, i))
            self.send_packet_out_multiple(self.name2switch[switch_name], pkts)
            sleep(self.lldp_interval)

    def periodic_l2_timeout_check(self, sw):
        sleep_time = 1

        while True:
            # need copy becuase length might change
            l2_mapping_tmp = self.l2_mapping[sw.name].copy()
            for mac in l2_mapping_tmp:
                if l2_mapping_tmp[mac]['added'] + self.l2_mapping_timeout < time():
                    self.deleteL2Entry(sw, mac)
            sleep(sleep_time)
