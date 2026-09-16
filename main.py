
import socket
import struct
import threading
import ipaddress
import subprocess
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar

DOIP_PORT = 13400
DOIP_VERSION = 0x02
DOIP_INV_VERSION = 0xFD
PT_VID_REQUEST = 0x0001
PT_VID_RESPONSE = 0x0004
PT_ROUTING_ACTIVATION_REQUEST = 0x0005
PT_ROUTING_ACTIVATION_RESPONSE = 0x0006
PT_ALIVE_CHECK_REQUEST = 0x0007
PT_ALIVE_CHECK_RESPONSE = 0x0008

def packet(ptype, payload=b""):
    return struct.pack("!BBHI", DOIP_VERSION, DOIP_INV_VERSION, ptype, len(payload)) + payload

def hx(b):
    return " ".join(f"{x:02X}" for x in b)

def parse(data):
    if len(data) < 8:
        return None
    v, iv, pt, ln = struct.unpack("!BBHI", data[:8])
    if len(data) < 8 + ln:
        return None
    return v, iv, pt, data[8:8+ln]

def clean(b):
    return "".join(chr(x) if 32 <= x < 127 else "." for x in b)

def parse_vehicle(p):
    if len(p) < 33:
        return {}
    return {
        "VIN": clean(p[:17]).strip(),
        "Logical Address": f"0x{int.from_bytes(p[17:19],'big'):04X}",
        "EID": hx(p[19:25]),
        "GID": hx(p[25:31]),
        "Further Action": f"0x{p[31]:02X}",
        "VIN/GID Sync": f"0x{p[32]:02X}",
    }

class StepRow(BoxLayout):
    def __init__(self, text, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(32), **kw)
        self.dot = Label(text="●", size_hint_x=None, width=dp(30), font_size="18sp")
        self.label = Label(text=text, halign="left")
        self.status = Label(text="WAIT", size_hint_x=None, width=dp(100))
        self.add_widget(self.dot)
        self.add_widget(self.label)
        self.add_widget(self.status)

    def set(self, status):
        self.status.text = status
        self.dot.text = "✓" if status == "OK" else ("✗" if status == "FAIL" else "●")

class DoIPRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(5), **kwargs)
        self.sock = None
        self.vehicle_ip = None
        self.vehicle_info = {}

        title = Label(text="[b]LEAPMOTOR DoIP TESTER[/b]", markup=True,
                      size_hint_y=None, height=dp(44), font_size="20sp")
        self.add_widget(title)

        net = GridLayout(cols=2, size_hint_y=None, height=dp(125), spacing=dp(5))
        net.add_widget(Label(text="Network:"))
        self.net_spinner = Spinner(text="Auto / Ethernet", values=("Auto / Ethernet", "Wi-Fi", "USB Ethernet", "Ethernet"))
        net.add_widget(self.net_spinner)
        net.add_widget(Label(text="Vehicle IP:"))
        self.ip = TextInput(multiline=False, hint_text="from DISCOVER")
        net.add_widget(self.ip)
        net.add_widget(Label(text="Tester SA (hex):"))
        self.sa = TextInput(text="0E80", multiline=False)
        net.add_widget(self.sa)
        net.add_widget(Label(text="Android interfaces:"))
        self.ifaces = Label(text=self.interfaces())
        net.add_widget(self.ifaces)
        self.add_widget(net)

        btns = GridLayout(cols=2, size_hint_y=None, height=dp(170), spacing=dp(6))
        self.bdiscover = Button(text="DISCOVER VEHICLE\nUDP 13400")
        self.bconnect = Button(text="TCP CONNECT\n13400")
        self.broute = Button(text="ROUTING ACTIVATION")
        self.balive = Button(text="ALIVE CHECK")
        self.bfull = Button(text="FULL TEST")
        self.bclear = Button(text="CLEAR LOG")
        for b in (self.bdiscover,self.bconnect,self.broute,self.balive,self.bfull,self.bclear):
            btns.add_widget(b)
        self.add_widget(btns)

        self.status = Label(text="READY", size_hint_y=None, height=dp(30))
        self.add_widget(self.status)

        steps = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(195))
        self.steps = {
            "ethernet": StepRow("Ethernet / network"),
            "udp": StepRow("DoIP UDP Discovery"),
            "vehicle": StepRow("Vehicle Announcement"),
            "tcp": StepRow("TCP 13400"),
            "routing": StepRow("Routing Activation"),
            "alive": StepRow("Alive Check"),
        }
        for x in self.steps.values():
            steps.add_widget(x)
        self.add_widget(steps)

        info_scroll = ScrollView(size_hint_y=None, height=dp(120))
        self.info = Label(text="Vehicle: not discovered", halign="left", valign="top")
        info_scroll.add_widget(self.info)
        self.add_widget(info_scroll)

        log_scroll = ScrollView()
        self.log = Label(text="", halign="left", valign="top", font_name="RobotoMono", font_size="11sp")
        log_scroll.add_widget(self.log)
        self.add_widget(log_scroll)

        self.bdiscover.bind(on_release=lambda *_: self.discover())
        self.bconnect.bind(on_release=lambda *_: self.connect())
        self.broute.bind(on_release=lambda *_: self.route())
        self.balive.bind(on_release=lambda *_: self.alive())
        self.bfull.bind(on_release=lambda *_: self.full_test())
        self.bclear.bind(on_release=lambda *_: setattr(self.log, "text", ""))

    def interfaces(self):
        try:
            return ", ".join(name for _, name in socket.if_nameindex()) or "Android"
        except:
            return "Android"

    def logmsg(self, s):
        Clock.schedule_once(lambda dt: self._log(s), 0)
    def _log(self, s):
        self.log.text += s + "\n"

    def stat(self, s):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", s), 0)

    def step(self, name, status):
        Clock.schedule_once(lambda dt: self.steps[name].set(status), 0)

    def discover(self):
        threading.Thread(target=self._discover, daemon=True).start()

    def _discover(self):
        self.stat("DISCOVER...")
        self.step("ethernet","OK")
        self.step("udp","WAIT")
        self.step("vehicle","WAIT")
        self.logmsg("\n=== 1. DOIP DISCOVERY ===")
        req = packet(PT_VID_REQUEST)
        self.logmsg("TX UDP 255.255.255.255:13400")
        self.logmsg(hx(req))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(1.5)
        found = 0
        try:
            s.bind(("",0))
            s.sendto(req, ("255.255.255.255", DOIP_PORT))
            self.step("udp","OK")
            while True:
                try:
                    data, addr = s.recvfrom(4096)
                except socket.timeout:
                    break
                self.logmsg(f"RX UDP {addr[0]}:{addr[1]}")
                self.logmsg(hx(data))
                p = parse(data)
                if p and p[2] == PT_VID_RESPONSE:
                    d = parse_vehicle(p[3])
                    d["IP"] = addr[0]
                    self.vehicle_info = d
                    self.vehicle_ip = addr[0]
                    self.ip.text = addr[0]
                    self.info.text = "\n".join(f"{k}: {v}" for k,v in d.items())
                    found += 1
                    self.step("vehicle","OK")
            if found:
                self.stat(f"FOUND {found} VEHICLE(S)")
            else:
                self.step("vehicle","FAIL")
                self.stat("NO DOIP VEHICLE")
                self.logmsg("No Vehicle Announcement. Check cable, RJ45, ignition and IP.")
        except Exception as e:
            self.step("udp","FAIL")
            self.logmsg("DISCOVER ERROR: " + repr(e))
            self.stat("DISCOVER ERROR")
        finally:
            s.close()

    def connect(self):
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        ip = self.ip.text.strip() or self.vehicle_ip
        if not ip:
            self.logmsg("Enter Vehicle IP or run DISCOVER.")
            return
        try:
            ipaddress.ip_address(ip)
            self.stat("TCP CONNECT...")
            self.logmsg(f"\n=== 2. TCP CONNECT {ip}:13400 ===")
            self.sock = socket.create_connection((ip,DOIP_PORT), timeout=3)
            self.sock.settimeout(3)
            self.step("tcp","OK")
            self.logmsg("TCP CONNECT: OK")
            self.stat("TCP CONNECTED")
        except Exception as e:
            self.step("tcp","FAIL")
            self.logmsg("TCP ERROR: "+repr(e))
            self.stat("TCP ERROR")

    def route(self):
        threading.Thread(target=self._route, daemon=True).start()

    def _route(self):
        if not self.sock:
            self._connect()
            if not self.sock: return
        try:
            sa = int(self.sa.text.strip(),16)
            if not 0 <= sa <= 65535: raise ValueError
        except:
            self.logmsg("Invalid Tester SA. Example 0E80")
            return
        payload = struct.pack("!HBI",sa,0,0)
        req = packet(PT_ROUTING_ACTIVATION_REQUEST,payload)
        self.logmsg("\n=== 3. ROUTING ACTIVATION ===")
        self.logmsg("TX TCP")
        self.logmsg(hx(req))
        try:
            self.sock.sendall(req)
            data = self.sock.recv(4096)
            self.logmsg("RX TCP")
            self.logmsg(hx(data))
            p = parse(data)
            if p and p[2] == PT_ROUTING_ACTIVATION_RESPONSE and len(p[3]) >= 9:
                code = p[3][4]
                self.logmsg(f"Response Code = 0x{code:02X}")
                self.step("routing","OK" if code in (0x00,0x01) else "FAIL")
                self.stat(f"ROUTING RESPONSE 0x{code:02X}")
            else:
                self.step("routing","FAIL")
                self.logmsg("Unexpected routing response.")
        except Exception as e:
            self.step("routing","FAIL")
            self.logmsg("ROUTING ERROR: "+repr(e))

    def alive(self):
        threading.Thread(target=self._alive, daemon=True).start()

    def _alive(self):
        if not self.sock:
            self.logmsg("TCP not connected.")
            return
        req = packet(PT_ALIVE_CHECK_REQUEST)
        self.logmsg("\n=== 4. ALIVE CHECK ===")
        self.logmsg("TX TCP")
        self.logmsg(hx(req))
        try:
            self.sock.sendall(req)
            data = self.sock.recv(4096)
            self.logmsg("RX TCP")
            self.logmsg(hx(data))
            p = parse(data)
            ok = bool(p and p[2] == PT_ALIVE_CHECK_RESPONSE)
            self.step("alive","OK" if ok else "FAIL")
            self.stat("ALIVE OK" if ok else "ALIVE FAIL")
        except Exception as e:
            self.step("alive","FAIL")
            self.logmsg("ALIVE ERROR: "+repr(e))

    def full_test(self):
        def run():
            self._discover()
            if self.vehicle_ip:
                self._connect()
                if self.sock:
                    self._route()
                    self._alive()
        threading.Thread(target=run, daemon=True).start()

class DoIPApp(App):
    def build(self):
        self.title = "Leapmotor DoIP Tester"
        return DoIPRoot()

if __name__ == "__main__":
    DoIPApp().run()
