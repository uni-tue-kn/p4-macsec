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

from __future__ import print_function
import nnpy
import struct

class PortMonitor:

    def __init__(self, queue, notification_socket, verbose = True):
        self.verbose = verbose
        self.queue = queue

        self.sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        self.sub.connect(notification_socket)
        self.sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')


    def monitor_messages(self):
        while True:
            msg = self.sub.recv()
            if self.verbose:
                print('-------')
                print(msg)
            msg_type = struct.unpack('4s', msg[:4])
            if msg_type[0] == 'PRT|':
                switch_id = struct.unpack('Q', msg[4:12])
                num_statuses = struct.unpack('I', msg[16:20])
                # wir betrachten immer nur den ersten Status
                port, status = struct.unpack('ii', msg[32:40])

                self.queue.put((switch_id, port, status))
                if self.verbose:
                    print('Port status change')
                    print('Switch ID: ' + str(switch_id[0]))
                    print('num_statuses: ' + str(num_statuses[0]))
                    print('port: ' + str(port))
                    print('status: ' + str(status))
