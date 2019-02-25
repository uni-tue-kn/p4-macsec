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
