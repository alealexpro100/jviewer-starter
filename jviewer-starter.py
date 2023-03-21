#! /usr/bin/env python
#
### Copyright 2017 Aaron Bulmahn (aarbudev@gmail.com)
### Copyright (C) 2021 ALEXPRO100 (alealexpro100@ya.ru)
### License: MIT

loginUrl="http://{0}/rpc/WEBSES/create.asp"
jnlpUrl = "http://{0}/Java/jviewer.jnlp?EXTRNIP={0}&JNLPSTR=JViewer"
powerUrl = "http://{0}/rpc/hostctl.asp?WEBVAR_POWER_CMD={1}&WEBVAR_FORCE_BIOS={2}"
jarBase = "http://{0}/Java/release/"
mainClass = "com.ami.kvm.jviewer.JViewer"

import argparse
from urllib.request import urlopen, urlretrieve, Request
from urllib.parse import urlencode
from http.client import IncompleteRead
import os, re, subprocess, platform, zipfile

from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showerror, showwarning, showinfo

class bmcRemote:
    def __init__(self, server: str):
        self.server=server
        self.sessionCookie=None
        self.path=None
    
    def getsession(self, username: str, password: str):
        credentials = {"WEBVAR_USERNAME": username, "WEBVAR_PASSWORD": password}
        loginRequest = Request(loginUrl.format(self.server))
        loginRequest.data = urlencode(credentials).encode("utf-8")
        loginResponse = urlopen(loginRequest).read().decode("utf-8")
        self.sessionCookie = re.search("'SESSION_COOKIE' : '([a-zA-Z0-9]+)'", loginResponse).group(1)
        
    def update_jars(self):
        base = jarBase.format(self.server)
        system = platform.system()
        if system == "Linux":
            natives = "Linux_x86_"
            path = os.environ.get("XDG_DATA_HOME")
        elif system == "Windows":
            natives = "Win"
            path = os.environ.get("LOCALAPPDATA")
        elif system == "Darwin":
            natives = "Mac"
            path = os.path.expanduser('~/Library/Application Support')
        else:
            raise Exception("OS not supported: " + system)
        natives += platform.architecture()[0][:2] + ".jar"
        path = os.path.join(path, "jviewer-starter", self.server)
        self.path = path

        if not os.path.exists(path):
            os.makedirs(path)
        for jar in ["JViewer.jar", "JViewer-SOC.jar", natives]:
            jar_path = os.path.join(path, jar)
            if not os.path.exists(jar_path):
                print("downloading %s -> %s" % (base + jar, jar_path))
                try:
                    urlretrieve(base + jar, jar_path)
                except Exception as e:
                    if jar=="JViewer-SOC.jar" and e.code==404:
                        print("Ignoring "+jar)
                        pass
                if jar == natives:
                    print("extracting %s" % jar_path)
                    with zipfile.ZipFile(jar_path, 'r') as natives_jar:
                        natives_jar.extractall(path)
        
    def run_jviewer(self):
        jnlpRequest = Request(jnlpUrl.format(self.server))
        jnlpRequest.add_header("Cookie", "SessionCookie=%s" % self.sessionCookie)
        try:
            jnlpResponse = urlopen(jnlpRequest).read().decode("utf-8")
        except IncompleteRead as e:
            # The server sends a wrong Content-length header. We just ignore it
            jnlpResponse = e.partial.decode("utf-8")

        args = ["java"]
        args.append("-Djava.library.path=" + self.path)
        args.append("-cp")
        args.append(os.path.join(self.path, "*"))
        args.append(mainClass)
        args += re.findall("<argument>([^<]+)</argument>", jnlpResponse)
        subprocess.Popen(args)
        
    def do_action(self, pwr_action: int, bios_action: int):
        powerRequest = Request(powerUrl.format(self.server, pwr_action, bios_action))
        powerRequest.add_header("Cookie", "SessionCookie=%s" % self.sessionCookie)
        urlopen(powerRequest)
        
class bmcGUI:
    def __init__(self, args) -> None:
        bmc = None
        self.root = Tk()
        self.server_input = StringVar(self.root)
        if args.server is not None:
            self.server_input.set(args.server)
        self.user_input = StringVar(self.root)
        if args.user is not None:
            self.user_input.set(args.user)
        self.pass_input = StringVar(self.root)
        if args.password is not None:
            self.pass_input.set(args.password)
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()
        ttk.Label(frm, text="Old iKVM").grid(column=0, row=0)
        ttk.Label(frm, text='Server IP').grid(column=0, row=1)
        ttk.Entry(frm, textvariable=self.server_input).grid(column=1, row=1)
        ttk.Label(frm, text='Username').grid(column=0, row=2)
        ttk.Entry(frm, textvariable=self.user_input).grid(column=1, row=2)
        ttk.Label(frm, text='Password').grid(column=0, row=3)
        ttk.Entry(frm, textvariable=self.pass_input).grid(column=1, row=3)
        self.session_button=ttk.Button(frm, text='Get session', command=self.initbmc)
        self.session_button.grid(column=3, row=1)
        self.jv_button=ttk.Button(frm, text='JViewer', command=self.startj)
        self.jv_button.grid(column=3, row=2)
        self.jv_button.state(["disabled"])
        self.bt_pwr_off=ttk.Button(frm, text="Power OFF", command=lambda: self.bmc.do_action(0, 0))
        self.bt_pwr_off.grid(column=4, row=0)
        self.bt_pwr_off.state(["disabled"])
        self.bt_pwr_on=ttk.Button(frm, text="Power ON", command=lambda: self.bmc.do_action(1, 0))
        self.bt_pwr_on.grid(column=4, row=1)
        self.bt_pwr_on.state(["disabled"])
        self.bt_reset=ttk.Button(frm, text="Reset", command=lambda: self.bmc.do_action(3, 0))
        self.bt_reset.grid(column=4, row=2)
        self.bt_reset.state(["disabled"])
        self.bt_reset_bios=ttk.Button(frm, text="Reset to BIOS", command=lambda: self.bmc.do_action(3, 1))
        self.bt_reset_bios.grid(column=4, row=3)
        self.bt_reset_bios.state(["disabled"])
        self.bt_shutdown=ttk.Button(frm, text="Shutdown", command=lambda: self.bmc.do_action(3, 1))
        self.bt_shutdown.grid(column=4, row=4)
        self.bt_shutdown.state(["disabled"])
        ttk.Button(frm, text="Quit", command=self.root.destroy).grid(column=0, row=4)
        self.root.mainloop()
    
    def initbmc(self):
        try:
            self.bmc = bmcRemote(self.server_input.get())
            self.bmc.getsession(self.user_input.get(), self.pass_input.get())
            self.bmc.update_jars()
            self.jv_button.state(["!disabled"])
            self.session_button.state(["disabled"])
            self.bt_pwr_off.state(["!disabled"])
            self.bt_pwr_on.state(["!disabled"])
            self.bt_reset.state(["!disabled"])
            self.bt_reset_bios.state(["!disabled"])
            self.bt_shutdown.state(["!disabled"])
        except Exception:
            showerror(title="Error", message="Could not get session or download jars.")
            
    def startj(self):
        try:
            self.bmc.run_jviewer()
        except Exception:
            showerror(title="Error", message="Could not start JViewer.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='jviewer-starter',
                    description='Program to use old IKVM.')
    parser.add_argument('-s', '--server')
    parser.add_argument('-u', '--user')
    parser.add_argument('-p', '--password')
    args = parser.parse_args()
    gui = bmcGUI(args)
    #bmc = bmcRemote(server=args.server)
    #bmc.getsession(args.user, args.password)
    #bmc.update_jars()
    #bmc.run_jviewer()
