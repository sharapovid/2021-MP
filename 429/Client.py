import socket
from tkinter import *
from tkinter import messagebox as mb
import time
import server_config as sc
import client_config as cc


class Client:
    def __init__(self, ip=cc.CLIENT_IP, port=cc.CLIENT_PORT):
        self._ip = ip
        self._port = port

    def RunSocket(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self.getAddress())
        self._sock.setblocking(False)
        print('Socket runned')
        print(f'[CURRENT CLIENT ADDRESS] {self.getAddress()}')
        
    def CloseSocket(self):
        self.getSocket().close()
        print('Socket closed')

    def getSocket(self):
        return self._sock

    def setAddress(self, ip: StringVar, port: StringVar, updateSock):
        if port.get() == sc.SERVER_PORT and ip.get() == sc.SERVER_IP:
            mb.showerror(title='ERROR', message='Client address cannot be equal to server address')
            return
        
        if ip.get() == '' and port.get() == '':
            return
        
        sock = self.getSocket()
        sock.sendto('!CHANGEADDRESS'.encode(cc.FORMAT), sc.CONN_ADDR)
        
        new_ip = ip.get()
        new_port = port.get()
        
        if new_ip == '':
            new_ip = self.getIP()
            
        if new_port == '':
            new_port = self.getPort()
        else:
            new_port = int(new_port)
                       
        self._ip = new_ip
        self._port = new_port
        self.CloseSocket()
        print('Restarting socket...')
        self.RunSocket()
        
        ip.set('')
        port.set('')
        
        sock = self.getSocket()
        sock.sendto(''.encode(cc.FORMAT), sc.CONN_ADDR)
        
        updateSock(sock)
    
    def getAddress(self):
        return self._ip, self._port
    
    def getIP(self):
        return self._ip

    def getPort(self):
        return self._port


class ConnectToServer:
    def __init__(self, addr=sc.CONN_ADDR):
        self._addr = addr

    def Connecting(self, sock: socket.socket):
        name = input('Please enter your nickname: ')
        if name != '':
            servAddr = self.getAddress()
            sock.setblocking(True)
            sock.sendto(name.encode(cc.FORMAT), servAddr)
            answer = int(sock.recv(8).decode(cc.FORMAT))
            
            if answer == -1:
                print('[ERROR] Unacceptable nickname!')
                sock.setblocking(False)
                name = self.Connecting(sock)
                return name
                
            elif answer == 0:
                print('[ERROR] Chosen nickname is taken, request rejected')
                sock.setblocking(False)
                name = self.Connecting(sock)
                return name

            elif answer == 1:
                sock.setblocking(False)
                print('Connected to server')
                return name
        else:
            name = cc.DEFAULT_NICKNAME
            servAddr = self.getAddress()
            sock.setblocking(True)
            sock.sendto(name.encode(cc.FORMAT), servAddr)
            answer = int(sock.recv(8).decode(cc.FORMAT))
            sock.setblocking(False)
            print('Connected to server')
            return name
    
    def getAddress(self):
        return self._addr


class Messenger:
    def __init__(self, nickname, sock: socket.socket):
        self._nickname = nickname
        self._sock = sock


    def loop(self, tk, log):
        log.see(END)
        try:
            sock = self.getSocket()
            message, addr = sock.recvfrom(1024)
            message = message.decode(cc.FORMAT)
            message += '\n'

            # Coloring server messages
            if addr == sc.CONN_ADDR:
                if message == '!KICK\n':
                    message = '[SERVER] You were kicked from the server'
                    log.insert(END, message, ('server_to_client'))
                    tk.after(5000, tk.quit)
                    return
                    
                log.insert(END, message, ('server_to_client'))
                
            elif message.startswith('[SERVER]'):
                log.insert(END, message, ('server_to_all'))
                
            else:
                log.insert(END, message, ('client_to_all'))
                
            tk.after(10, self.loop, tk, log)
        except BlockingIOError:
            tk.after(10, self.loop, tk, log)


    def send(self, nickname, text):
        sock = self.getSocket()
        old_name = self.getNickname()
        name = nickname.get()

        if name != old_name:
            while True:
                try:
                    sock.sendto('!CHANGENAME'.encode(cc.FORMAT), sc.CONN_ADDR)
                    sock.setblocking(True)
                    sock.sendto(name.encode(cc.FORMAT), sc.CONN_ADDR)
                    answer = sock.recv(8).decode(cc.FORMAT)
                    sock.setblocking(False)

                    if answer == '0' or answer == '-1':   # nickname is taken or unacceptable
                        nickname.set(old_name)
                        break

                    self.setNickname(name)
                    break
                except BlockingIOError:
                    time.sleep(1)

        message = '%s' % text.get()
        sock.sendto(message.encode(cc.FORMAT), sc.SERVER_ADDR)
        text.set('')


    def setNickname(self, nickname):
        self._nickname = nickname


    def getNickname(self):
        return self._nickname
    
    
    def getSocket(self):
        return self._sock


    def updateSock(self, sock: socket.socket):
        self._sock = sock
        
        
class ClientWindow:
    def __init__(self, setAddress: Client.setAddress, updateSock: Messenger.updateSock,
                 title=cc.TITLE, size=cc.SIZE, defaultName=cc.DEFAULT_NICKNAME):
        self._tk = Tk()
        self._tk['bg'] = 'LightGray'
        self._tk.title(title)
        self._tk.geometry(size)
        self._tk.resizable(width=False, height=False)
        
        main_f1 = Frame(master=self._tk, bg='LightGray')
        main_f1.pack(fill='both', expand=1)
        
        main_f2 = Frame(master=self._tk, bg='LightGray')
        main_f2.pack(fill='both', expand=1)


        # ---> <Log> <---
        self._log = Text(master=main_f1, bg='LightGray', wrap=WORD)
        self._log.tag_config('server_to_all', foreground='Red')
        self._log.tag_config('server_to_client', foreground='Indigo')
        self._log.tag_config('client_to_all', foreground='Blue')
        
        self._log.pack(fill='both', expand=1)
        
        
        # ---> <Nickname and message input fields> <---
        frame = Frame(master=main_f2)
        frame.pack(side='left', fill='x', expand=1)
        
        self._nickname = StringVar()
        self._nickname.set(defaultName)
        self._text = StringVar()
        self._text.set('')

        self._nick = Entry(master=frame, textvariable=self._nickname, bg='Silver')
        self._msg = Entry(master=frame, textvariable=self._text, bg='Silver')

        self._nick.pack(fill='both', expand=1)
        self._msg.pack(fill='both', expand=1)

        self._msg.focus_set()
        
        
        # ---> <Options> button <---
        b1 = Button(master=main_f2, text='Options', bg='Silver', fg='red',
                    activebackground='LightGray', activeforeground='red',
                    font=('TkDefaultFont', 11, 'normal'), bd=0, padx=60, pady=25,
                    command=lambda: self.openOptionsWindow(self._tk, setAddress, updateSock))
        b1.pack(side='left', fill='both', padx=5, pady=5)
                        
    
    def openOptionsWindow(self, tk, setAddress: Client.setAddress, 
                          updateSock: Messenger.updateSock):
        
        options = Toplevel(tk, bg='Silver', padx=10, pady=10)
        options.title('Options')
        options.geometry('200x150+300+300')
        options.resizable(width=False, height=False)

        
        f_b_label1 = Label(master=options, text='Connection settings', 
                          font=('TkDefaultFont', 11, 'normal'), 
                          fg='red', bg='Silver')
        
        f_b_label2 = Label(master=options, bg='Silver')
        
        f_b_label1.pack()
        f_b_label2.pack()
        
        f_ip_entry = Frame(master=options, bg='Silver')
        f_port_entry = Frame(master=options, bg='Silver')
        
        ip_label_b = Label(master=f_ip_entry, text='IP:\t', 
                           fg='DarkBlue', bg='Silver', bd=1)
        port_label_b = Label(master=f_port_entry, text='Port:\t', 
                             fg='DarkBlue', bg='Silver', bd=1)
        
        ip_b = StringVar()
        port_b = StringVar()
        
        ip_entry_b = Entry(master=f_ip_entry, textvariable=ip_b,
                           justify='center', bg='LightGray')
        port_entry_b = Entry(master=f_port_entry, textvariable=port_b, 
                             justify='center', bg='LightGray')
        
        b = Button(master=options, text='Change', bg='DarkGray', fg='red',
                   activebackground='Silver', activeforeground='red',
                   font=('TkDefaultFont', 11, 'normal'), bd=0, height=2,
                    command=lambda: setAddress(ip_b, port_b, updateSock))
        
        ip_label_b.pack(side='left', fill='x')
        ip_entry_b.pack(side='left', fill='x')
        
        port_label_b.pack(side='left', fill='x')
        port_entry_b.pack(side='left', fill='x')
        
        f_ip_entry.pack()
        f_port_entry.pack(pady=5)
        
        b.pack(fill='both', expand=1)
        
        
    def getTK(self):
        return self._tk

    def getLog(self):
        return self._log

    def getNickname(self):
        return self._nickname

    def getText(self):
        return self._text

    def getMessage(self):
        return self._msg
        
        
if __name__ == '__main__':

    client = Client()
    client.RunSocket()
    sock = client.getSocket()
    
    connection = ConnectToServer()
    nickname = connection.Connecting(sock)

    messenger = Messenger(nickname, sock)
    
    window = ClientWindow(client.setAddress, messenger.updateSock, defaultName=nickname)
    nickname = window.getNickname()

    msg = window.getMessage()
    text = window.getText()
    msg.bind('<Return>', 
             lambda event: messenger.send(nickname, text))


    tk = window.getTK()
    log = window.getLog()
    tk.after(1, messenger.loop, tk, log)
    tk.mainloop()
    client.getSocket().sendto('!DISCONNECT'.encode(cc.FORMAT), sc.CONN_ADDR)