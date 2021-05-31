#
#This is the Controller. 
#it handles the SSH connections out to the devices.
#it uses Netmiko.
#should this be one or more classes, or just functions

import netmiko
import os

SCPSERVER = "10.97.31.235"

class RemoteRouter():
    """create a router object for Netmiko. """
    def __init__(self,loginID,ipAddy='', devDict=''):
        connect = True
       
        #I want SCP Server and NTP Server to be global constants set once in main.

        if ipAddy or devDict:
            self.ipAddy = ipAddy
            self.loginuser=loginID[0]
            self.loginpass=loginID[1]
            self.SCPSERVER = "10.97.31.235"
            self.NTPSERVER = "10.97.31.20"
            self.cactiserver = "10.97.31.35"
            
        if devDict:
            print("found Dev Dictionary")
            self.ipAddy=devDict['IPADDY']    
            self.devDict = devDict
        else:    
            print("initialze blank dict in RemoteRouter init")
            self.devDict = {'IPADDY':ipAddy, 'CONNECT':'', 'HOSTNAME':'','SHVER':'','DIRFLASH':'','SHIPINTBRI':'',
            'SHCELL':'','UPTIME':'','VERSION':'','MODELNUM':'','SERIALNUM':'','CONFREG':''}

        routername = ""
        try:
            net_connect = self.connectToRouter(self.ipAddy)
            if net_connect=="no connect":
                connect=False
        except:
            print("no connection to ", self.ipAddy)
            connect=False


        if connect:
            routername = self.getHostname(net_connect)
            if routername == "":
                print("unable to connect to remote router")
            else:    
                print("remoterouter is ", routername)
                status = self.getDevDetails(net_connect)

                if not ('commandoversms.tcl' in self.devDict['DIRFLASH']):
                    print("command over sms is missing")
                else:
                        print("command over sms is in flash:")

                
                if not ('datak9' in self.devDict['SHVER']):
                    print("needs license for IP SLA")    
                else:
                    print("license file okay")        

                self.devDict['HOSTNAME'] = routername
        else:
            print("no connection to router")       
        

    def connectToRouter(self, ipAddy):
        """this is the basic router connection for this program"""
        #
        cisco = {
            'device_type': 'cisco_ios',
            'host': ipAddy,
            'username': self.loginuser,
            'password': self.loginpass,
            }
        
        try:
            net_connect = netmiko.ConnectHandler (**cisco)
            
        except:
            print("unable to connect to host-connectToRouter")    
            return("no connect")

        return (net_connect)              
    #end connectToRouter

    def getDevDetails(self, net_connect):
        print("inside getDevDetails")
        try:
            self.devDict['SHIPINTBRI'] = net_connect.send_command('sh ip int brie')
            print( self.devDict['SHIPINTBRI'] )
            self.devDict['SHVER'] = self.ShowVer(net_connect)
            print( self.devDict['SHVER'])
            print("end sh ver")
            privlevel = net_connect.send_command('show priv')
            self.devDict['DIRFLASH'] = self.getFilenames(net_connect)
            print("dir flash: is ")
            print( self.devDict['DIRFLASH'])

        except:
            print("unable to connect to host-connectToRouter")    
            return("no connect")

        return("OK")       
 
    def ShowVer(self,net_connect):
        getver=net_connect.send_command('sh version')
        print(getver) 
        return(getver)  

    def getHostname(self,net_connect):
        #
        privlevel = net_connect.send_command('show priv')
        print("priv level is ",privlevel)
        if privlevel=="Current privilege level is 15":
            hostname = net_connect.send_command('sh run | inc host')
            self.hostname = hostname[9:]
            print("hostname is ", self.hostname)
        else:
            print("insufficient Privilege Level")  
            self.hostname=''  
        return(self.hostname)

    def getFilenames(self, net_connect):
        dirflash = net_connect.send_command('dir flash:')
        
        return(dirflash)

    def sendConfigScript(self,ipAddy, cmdlist, log=True):
        """this method sends a group of config commands to the router using config mode"""
        
        print("inside sendScript")
        net_connect = self.connectToRouter(ipAddy)
        log = net_connect.send_config_set(cmdlist)
        print("log in sendscript is ", log)
        return(log)

    def sendEnableScript(self, ipAddy, cmdlist, log=True):
        """this method sends a list of enable commands to the 
            router using enable mode. method splits up the list
            and sends commands one-at-a-time """
        loglist = []
        print("inside sendScript")
        net_connect = self.connectToRouter(ipAddy)
        for cmd in cmdlist:
            log = net_connect.send_command(cmd)
            print("log in sendscript is ", log)
            loglist.append(log)
        print(loglist)
        return(loglist)

    def copySCP(self, ipAddy, sourceIP, destIP, filelist):
        """method to copy to/from scp server
            bring in filelist, even if it is a one-element list"""
        net_connect = self.connectToRouter(ipAddy)
        if ipAddy==sourceIP:
            for filename in filelist:
                print("copying ", filename, " to SCP Server ", destIP)
                copycmd="copy flash:{0} scp:{1}" .format(filename,destIP)
                print("copy command ", copycmd)
                response = net_connect.send_command(copycmd, expect_string=r']?')
                response = net_connect.send_command(self.SCPSERVER, expect_string=r']?')
                response = net_connect.send_command(self.loginuser, expect_string=r']?')
                response = net_connect.send_command(filename, expect_string=r'Password:')
                response = net_connect.send_command_timing(self.loginpass)
                if 'copied' in response:
                    print("copy command completed ", filename)
        else:
            for filename in filelist:
                print("copying ", filename, " from SCP Server ", sourceIP)
                copycmd="copy scp:{0} flash:{1}" .format(sourceIP, filename)
                print("copy command ", copycmd)
               # response = net_connect.send_command(copycmd, expect_string=r']?')
                # response = net_connect.send_command(self.SCPSERVER, expect_string=r']?')
                # response = net_connect.send_command(self.loginuser, expect_string=r']?')
                # response = net_connect.send_command(filename, expect_string=r'Password:')
                # response = net_connect.send_command_timing(self.loginpass)
                # if 'copied' in response:
                #     print("copy command completed ", filename)

                    # example on router
                    # SCADA-NORTH-CRITSPARE158#copy scp:10.97.31.35/commandoversms.tcl flash:
                    # Address or name of remote host [10.97.31.35]?
                    # Source username [dougs.admin]?
                    # Source filename [10.97.31.35/commandoversms.tcl]? commandoversms.tcl
                    # Destination filename [commandoversms.tcl]?
                    # %Warning:There is a file already existing with this name
                    # Do you want to over write? [confirm]y
                    # Password:




if __name__ == "__main__":
    print ("controller is main")
    loginuser = 'dougs.admin'
    loginpass = input("password:")
    testloginID=(loginuser,loginpass)
    ipAddy="192.168.20.14"
    print("working dir is ", os.getcwd())
    router_ssh = RemoteRouter(testloginID, ipAddy)
    #router_ssh.copySCP(ipAddy,ipAddy,SCPSERVER,['commandoversms.tcl'])
    router_ssh.copySCP(ipAddy,'10.97.31.35',ipAddy,['commandoversms.tcl'])





    #there is a dedicated set of functions for copy SCP
    #but since I am only doing 809 routers, the benefit compared
    #to the effort seemed marginal