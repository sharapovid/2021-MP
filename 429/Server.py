from abc import abstractmethod
import socket
from tkinter import * 
from tkinter import messagebox as mb
import threading, time
import server_config as sc

class Server:
    def __init__(self, ip=sc.SERVER_IP, port=sc.SERVER_PORT):
        self._ip = ip
        self._port = port

    def RunSocket(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.bind(self.getAddress())
            self._sock.setblocking(False)
            print('Socket runned')
            print(f'[CURRENT SERVER ADDRESS] {self.getAddress()}')
        except:
            print('[ERROR] Socket startup error\n')

    def CloseSocket(self):
        self.getSocket().shutdown(socket.SHUT_RDWR)
        self.getSocket().close()
        print('Socket closed')

    def setPort(self, port):
        if port == '':
            mb.showinfo(title='Error', message='Invalid input')
            return
        
        with open('server_config.py', 'r+') as conf:
            lines = conf.readlines()
            conf.seek(0)
            for line in lines:
                if line.startswith('SERVER_PORT'):
                    conf.write(f'SERVER_PORT = {port}\n')
                else:
                    conf.write(line)
            
        msg = '[SERVER] Server restarts, please, try to reconnect after a few minutes'
        self.getSocket().sendto(msg.encode(sc.FORMAT), self.getAddress())
        print('Please, restart the server')
        
    def getSocket(self):
        return self._sock
    
    def getAddress(self):
        return self._ip, self._port
    
    def getIP(self):
        return self._ip

    def getPort(self):
        return self._port


class Connections:
    def __init__(self, addr=sc.CONN_ADDR):
        self._addr = addr
        self._sock = 0

    def RunSocket(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.bind(self.getAddress())
            self._sock.setblocking(False)
            print('The server is waiting for clients')
        except:
            print('[ERROR] Connections socket startup error\n')

    def getSocket(self):
        return self._sock

    def getAddress(self):
        return self._addr
    
    def getIP(self):
        return self._addr[0]

    def getPort(self):
        return self._addr[1]


class Filter:
    def __init__(self, words: set):
        for word in words:
            lower_word = word.lower()
            words.remove(word)
            words.add(lower_word)
            
        self._words = set()
        self._words.update(words)
    

    def filter(self, msg: str):
        indexes = self.string_upper_indexes(msg)
        msg = msg.lower()
        
        for word in self.getKeywords():
            if msg.find(word) != -1:
                msg = msg.replace(word, '*'*len(word))
                
        msg = self.upper_string_by_indexes(msg, indexes)
        return msg
                             
                                
    def addKeyword(self, keyword: StringVar):
        self.getKeywords().add(keyword.get().lower())
        keyword.set('')
    
    
    def removeKeyword(self, keyword: StringVar):
        self.getKeywords().discard(keyword.get().lower())
        keyword.set('')
        
        
    def getKeywords(self):
        return self._words
    
    
    def showKeywords(self):
        words_list = list()
        words = self.getKeywords()
        
        if words == set():
            words_list = 'No keywords found'
        else:
            for word in words:
                if (len(words_list) + 1) % 3 == 0:
                    word += '\n'
                    words_list.append(word)
                else:
                    word += '\t'
                    words_list.append(word)
                    
        words_list = ''.join(words_list)                   
        mb.showinfo(title='Keywords', message=words_list)
    
    
    def check(self, s: str):
        if s == '' or s.isnumeric() or s.find(' ') != -1 or s.find('!') != -1:
            return True
        
        s = s.lower()
        for word in self.getKeywords():
            if s.find(word) != -1:
                return True
        return False


    def string_upper_indexes(self, s: str):
        indexes = []
        for i in range(len(s)):
            if(s[i].isupper()):
                indexes.append(i)
        return indexes
    
    
    def upper_string_by_indexes(self, s: str, indexes: list):
        char_list = list(s)
        for i in indexes:
            char_list[i] = char_list[i].upper()
        s = ''.join(char_list)
        return s
    

class ClientsData:
    def __init__(self, name, addr):
        self._nickname = name
        self._addr = addr

    def getData(self):
        return (self._nickname, self._addr)

    def getNickname(self):
        return self._nickname

    def getAddress(self):
        return self._addr


class ClientsList:
    def __init__(self, sock: socket.socket):
        self._clients = set()
        self._sock = sock

    def recvClients(self, msg_filter: Filter):
        sock = self.getSocket()
        thread = threading.currentThread()
        # Using getattr to stop the looping thread correctly
        while getattr(thread, "do_run", True):
            try:
                name, addr = sock.recvfrom(1024)
                name = name.decode(sc.FORMAT)
                clients = self.getClients()
           
                result = self.isAdded(addr)
                if result:
                    if name == '!DISCONNECT':
                        name = self.getNameByAddr(addr)
                        clients.remove((name, addr))
                        msg1 = f'[SERVER] {name} disconnected from the server!\n'
                        msg2 = f'[SERVER] Now connected: {len(clients)} users'
                        message = msg1 + msg2
                        sock.sendto(message.encode(sc.FORMAT), sc.SERVER_ADDR)
                        continue

                    if name == '!CHANGENAME':
                        sock.setblocking(True)
                        new_name = sock.recv(1024).decode(sc.FORMAT)

                        if msg_filter.check(new_name):
                            sock.sendto('-1'.encode(sc.FORMAT), addr)
                            message = '[ERROR] Unacceptable nickname!'
                            sock.sendto(message.encode(sc.FORMAT), addr)  # Saying to the client about error
                            sock.setblocking(False)
                            continue
                        
                        elif self.isTheNameTaken(new_name):
                            sock.sendto('0'.encode(sc.FORMAT), addr)
                            message = '[ERROR] Chosen nickname is taken, request rejected'
                            sock.sendto(message.encode(sc.FORMAT), addr)
                            sock.setblocking(False)
                            continue

                        old_name = self.setNameByAddr(addr, new_name)
                        message = f'[SERVER] {old_name} changed his nickname to {new_name}!'
                        sock.sendto(message.encode(sc.FORMAT), sc.SERVER_ADDR)
                        sock.sendto('1'.encode(sc.FORMAT), addr)   # Saying to the client that the name changed
                        sock.setblocking(False)
                    
                    if name == '!CHANGEADDRESS':
                        old_addr = addr
                        sock.setblocking(True)
                        _, new_addr = sock.recvfrom(1024)
                        self.changeAddr(old_addr, new_addr)
                        sock.setblocking(False)
                    continue

                else:
                    if msg_filter.check(name):
                        sock.sendto('-1'.encode(sc.FORMAT), addr)  # Unacceptable nickname
                        continue

                    elif self.isTheNameTaken(name):
                        sock.sendto('0'.encode(sc.FORMAT), addr)   # Saying to the client that the name taken
                        continue

                    else:
                        new_client = ClientsData(name, addr)
                        clients.add(new_client.getData())
                        sock.sendto('1'.encode(sc.FORMAT), addr)    # Saying to the client that he's connected
                        msg1 = f'[SERVER] {name} connected to the server!\n'
                        msg2 = f'[SERVER] Now connected: {len(clients)} users'
                        message = msg1 + msg2
                        sock.sendto(message.encode(sc.FORMAT), sc.SERVER_ADDR)

            except BlockingIOError:
                time.sleep(1)            
            except socket.error:
                time.sleep(3)


    def getSocket(self):
        return self._sock


    def isAdded(self, addr):
        clients = self.getClients()
        for client in clients:
            if client[1] == addr:
                return True
        return False


    def getClients(self):
        return self._clients
    
    
    def getClientByName(self, name):
        for client in self.getClients():
            if client[0] == name:
                return client
            
            
    def Kick(self, name: StringVar):
        try:
            client = self.getClientByName(name.get())
            sock = self.getSocket()
            sock.sendto('!KICK'.encode(sc.FORMAT), client[1])
            name.set('')
        except TypeError:
            name.set('')
            mb.showinfo(title='Error', message='No such client found')
        
            
    def showClients(self):
        clients_list = ''
        clients = self.getClients()
        
        if clients == set():
            clients_list = 'No connected clients found'
        else:
            for client in clients:
                clients_list += '%s\n' % client[0]
            
        mb.showinfo(title='Connected clients', message=clients_list)        
    
    
    def isTheNameTaken(self, sample):
        clients = self.getClients()
        for client in clients:
            if client[0] == sample:
                return True
        return False
    
    
    def setNameByAddr(self, addr, new_name):
        clients = self.getClients()
        for client in clients:
            if client[1] == addr:
                old_name = client[0]
                new_client = list(client)
                new_client[0] = new_name
                new_client = tuple(new_client)
                clients.remove(client)
                clients.add(new_client)
                return old_name


    def getNameByAddr(self, addr):
        for client in self.getClients():
            if client[1] == addr:
                return client[0]
        return '!NAME_ERROR'


    def changeAddr(self, old_addr, new_addr):
        clients = self.getClients()
        for client in clients:
            if client[1] == old_addr:
                new_client = list(client)
                new_client[1] = new_addr
                new_client = tuple(new_client)
                clients.remove(client)
                clients.add(new_client)
                return


class ServerWindow:
    def __init__(self, setPort: Server.setPort, Kick: ClientsList.Kick, 
                 showClients: ClientsList.showClients, showKeywords: Filter.showKeywords,
                 addKeyword: Filter.addKeyword, removeKeyword: Filter.removeKeyword,
                 title=sc.TITLE, size=sc.SIZE):
        
        self._tk = Tk()
        self._tk.title(title)
        self._tk.geometry(size)
        self._tk.resizable(width=False, height=False)
        
        main_f1 = Frame(master=self._tk)
        main_f1_label = Label(master=main_f1, text='Connections Settings', 
                              font=('TkDefaultFont', 12, 'normal'), fg='red')
        main_f1.pack(expand=1)
        main_f1_label.pack()
        
        main_f2 = Frame(master=self._tk)
        main_f2_label = Label(master=main_f2, text='Filter Settings', 
                              font=('TkDefaultFont', 12, 'normal'), fg='red')
        main_f2.pack(expand=1)
        main_f2_label.pack()
        
        
        # ---> <Change port> button <---
        f_b1 = Frame(master=main_f1, bg='LightGray', padx=5, pady=5)
        f_b1.pack(side='left', padx=5, pady=5)
        
        label_b1 = Label(master=f_b1, text='Port', bg='LightGray')
        
        text_b1 = StringVar()
        entry_b1 = Entry(master=f_b1, textvariable=text_b1, justify='center')
        
        b1 = Button(master=f_b1, text='Change port', height=2)
        b1.config(command=lambda: setPort(text_b1.get()))
        
        label_b1.pack(fill='x')
        entry_b1.pack(fill='x')
        b1.pack(fill='x')
                        
                
        # ---> <Connected clients> button <---
        f_b2 = Frame(master=main_f1, bg='LightGray', padx=6, pady=6)
        f_b2.pack(side='left', padx=5, pady=5)
        
        label_b2 = Label(master=f_b2, text='Connected clients', bg='LightGray')
        entry_b2 = Entry(master=f_b2, bd=0, state='disabled',
                         cursor='arrow', disabledbackground='LightGray')
        
        b2 = Button(master=f_b2, text='Show', height=2)
        b2.config(command=showClients)
        
        label_b2.pack(fill='x')
        entry_b2.pack(fill='x')
        b2.pack(fill='x')
                
                
        # ---> <Kick client> button <---
        f_b3 = Frame(master=main_f1, bg='LightGray', padx=5, pady=5)
        f_b3.pack(side='left', padx=5, pady=5)
        
        label_b3 = Label(master=f_b3, text='Client name', bg='LightGray')
        
        text_b3 = StringVar()
        entry_b3 = Entry(master=f_b3, textvariable=text_b3, justify='center')
        
        b3 = Button(master=f_b3, text='Kick client', height=2)
        b3.config(command=lambda: Kick(text_b3))
        
        label_b3.pack(fill='x')
        entry_b3.pack(fill='x')
        b3.pack(fill='x')
        
        
        # ---> <Filter keywords> button <---
        f_b4 = Frame(master=main_f2, bg='LightGray', padx=6, pady=6)
        f_b4.pack(side='left', padx=5, pady=5)
        
        label_b4 = Label(master=f_b4, text='Filter keywords', bg='LightGray')
        entry_b4 = Entry(master=f_b4, bd=0, state='disabled',
                         cursor='arrow', disabledbackground='LightGray')

        
        b4 = Button(master=f_b4, text='Show', height=2)
        b4.config(command=showKeywords)
        
        label_b4.pack(fill='x')
        entry_b4.pack(fill='x')
        b4.pack(fill='x')
        
        
        # ---> <Add keyword> button <---
        f_b5 = Frame(master=main_f2, bg='LightGray', padx=5, pady=5)
        f_b5.pack(side='left', padx=5, pady=5)
        
        label_b5 = Label(master=f_b5, text='Add keyword', bg='LightGray')
        
        text_b5 = StringVar()
        entry_b5 = Entry(master=f_b5, textvariable=text_b5, justify='center')
        
        b5 = Button(master=f_b5, text='Add', height=2)
        b5.config(command=lambda: addKeyword(text_b5))
        
        label_b5.pack(fill='x')
        entry_b5.pack(fill='x')
        b5.pack(fill='x')
        
        
        # ---> <Remove keyword> button <---
        f_b6 = Frame(master=main_f2, bg='LightGray', padx=5, pady=5)
        f_b6.pack(side='left', padx=5, pady=5)
        
        label_b6 = Label(master=f_b6, text='Remove keyword', bg='LightGray')
        
        text_b6 = StringVar()
        entry_b6 = Entry(master=f_b6, textvariable=text_b6, justify='center')
        
        b6 = Button(master=f_b6, text='Remove', height=2)
        b6.config(command=lambda: removeKeyword(text_b6))
        
        label_b6.pack(fill='x')
        entry_b6.pack(fill='x')
        b6.pack(fill='x')
        
        
    def getTK(self):
        return self._tk


class ChatLog:
    def __init__(self, file_path):
        self._file_path = file_path


    def createNewLogFile(self):
        with open(self.getPath(), 'w'):
            return
        
        
    def writeLine(self, line: str):
        with open(self.getPath(), 'a') as log:
            print(line, file=log)
                    

    def getPath(self):
        return self._file_path


class Messenger:
    def __init__(self):
        pass

    def loop(self, tk: Tk, sock: socket.socket, List: ClientsList, 
             msg_filter: Filter, writeLine: ChatLog.writeLine):
        try:
            message, addr = sock.recvfrom(1024)
            message = message.decode(sc.FORMAT)
            clients = List.getClients()
            
            nickname = List.getNameByAddr(addr)

            if addr == sc.CONN_ADDR or addr == sc.SERVER_ADDR:
                message = bytes(message, sc.FORMAT)        
                        
            elif message == '':
                tk.after(10, self.loop, tk, sock, List, msg_filter, writeLine)
                return
            else:
                current_time = time.strftime('%H:%M:%S', time.localtime())
                message = msg_filter.filter(f'[{current_time}] {nickname}: {message}')
                message = bytes(message, sc.FORMAT)
                
            writeLine(message.decode(sc.FORMAT))
            
            for client in clients:
                sock.sendto(message, client[1])
                
            if addr != sc.SERVER_ADDR:
                tk.after(10, self.loop, tk, sock, List, msg_filter, writeLine)
            else:
                tk.after(10, tk.destroy)
                
        except BlockingIOError:
            tk.after(10, self.loop, tk, sock, List, msg_filter, writeLine)


if __name__ == '__main__':
    server = Server()
    server.RunSocket()
    connections = Connections()
    connections.RunSocket()

    servSock = server.getSocket()
    servPort = server.getPort()
    connSock = connections.getSocket()
    connPort = connections.getPort()

    m = Messenger()
    List = ClientsList(connSock)
    msg_filter = Filter({'[SERVER]', 'nigger', 'Bob', 'shit', 'Doggo'})
    chat_log = ChatLog('log.txt')
    chat_log.createNewLogFile()

    thread = threading.Thread(target=List.recvClients, args=(msg_filter,))
    thread.start()
    
    window = ServerWindow(server.setPort, List.Kick, List.showClients,
                          msg_filter.showKeywords, msg_filter.addKeyword,
                          msg_filter.removeKeyword)
    tk = window.getTK()

    tk.after(1, m.loop, tk, servSock, List, msg_filter, chat_log.writeLine)
    tk.mainloop()
    thread.do_run = False