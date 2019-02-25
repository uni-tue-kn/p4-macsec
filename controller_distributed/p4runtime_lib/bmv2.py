# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from switch import SwitchConnection
from p4.tmp import p4config_pb2


def buildDeviceConfig(bmv2_json_file_path=None, port=None, notifications=None, cpu_iface=None):
    "Builds the device config for BMv2"
    device_config = p4config_pb2.P4DeviceConfig()
    device_config.reassign = True
    # (*kv)["port"] = "9090";
    # (*kv)["notifications"] = "ipc:///tmp/bmv2-0-notifications.ipc";
    # (*kv)["cpu_iface"] = "veth251";
    #device_config.extras.kv["port"] = port
    #device_config.extras.kv["notifications"] = notifications
    #device_config.extras.kv["cpu_iface"] = cpu_iface
    #print(device_config)
    with open(bmv2_json_file_path) as f:
        device_config.device_data = f.read()
    return device_config


class Bmv2SwitchConnection(SwitchConnection):
    def buildDeviceConfig(self, **kwargs):
        return buildDeviceConfig(**kwargs)
    def __repr__(self):
        return "name: {0}, address {1}, device_id: {2}".format(self.name, self.address, self.device_id)
