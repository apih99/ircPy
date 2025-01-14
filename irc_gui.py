#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
from irc_client import IRCClient, IRCMessage
from datetime import datetime
import queue

class IRCGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IRC Client")
        self.root.geometry("1000x600")
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('Channel.TFrame', background='#2b2b2b')
        self.style.configure('Chat.TFrame', background='#1e1e1e')
        self.style.configure('Users.TFrame', background='#2b2b2b')
        
        # IRC Client setup
        self.irc = None
        self.message_queue = queue.Queue()
        self.connected = False
        
        # Add message history
        self.message_history = {}
        self.current_channel = None
        
        # Create GUI elements
        self.create_menu()
        self.create_connection_frame()
        self.create_main_interface()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start message processing
        self.root.after(100, self.process_message_queue)

    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Connect", command=self.show_connection_frame)
        file_menu.add_command(label="Disconnect", command=self.disconnect)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Channel menu
        channel_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Channel", menu=channel_menu)
        channel_menu.add_command(label="Join Channel", command=self.show_join_dialog)
        channel_menu.add_command(label="Leave Channel", command=self.part_current_channel)

    def create_connection_frame(self):
        """Create the connection dialog"""
        self.conn_frame = ttk.Frame(self.root, padding="10")
        self.conn_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        
        # Server details
        ttk.Label(self.conn_frame, text="Server:").grid(row=0, column=0, padx=5, pady=5)
        self.server_var = tk.StringVar(value="irc.libera.chat")
        ttk.Entry(self.conn_frame, textvariable=self.server_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.port_var = tk.StringVar(value="6667")
        ttk.Entry(self.conn_frame, textvariable=self.port_var).grid(row=0, column=3, padx=5, pady=5)
        
        # Nickname
        ttk.Label(self.conn_frame, text="Nickname:").grid(row=1, column=0, padx=5, pady=5)
        self.nick_var = tk.StringVar(value="IRCPyUser")
        ttk.Entry(self.conn_frame, textvariable=self.nick_var).grid(row=1, column=1, padx=5, pady=5)
        
        # Connect button
        ttk.Button(self.conn_frame, text="Connect", command=self.connect).grid(row=1, column=2, columnspan=2, pady=10)

    def create_main_interface(self):
        """Create the main chat interface"""
        # Channel list (left panel)
        self.channels_frame = ttk.Frame(self.root, style='Channel.TFrame', padding="5")
        self.channels_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.channels_frame.grid_rowconfigure(0, weight=1)
        self.channels_frame.grid_columnconfigure(0, weight=1)
        
        self.channel_list = ttk.Treeview(self.channels_frame, show="tree", selectmode="browse")
        self.channel_list.grid(row=0, column=0, sticky="nsew")
        self.channel_list.bind('<<TreeviewSelect>>', self.on_channel_select)
        
        # Chat area (center panel)
        self.chat_frame = ttk.Frame(self.root, style='Chat.TFrame')
        self.chat_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#ffffff')
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.message_input = ttk.Entry(self.input_frame)
        self.message_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.message_input.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(self.input_frame, text="Send", command=lambda: self.send_message(None))
        self.send_button.grid(row=0, column=1)
        
        # User list (right panel)
        self.users_frame = ttk.Frame(self.root, style='Users.TFrame', padding="5")
        self.users_frame.grid(row=1, column=2, sticky="nsew", padx=2, pady=2)
        self.users_frame.grid_rowconfigure(0, weight=1)
        self.users_frame.grid_columnconfigure(0, weight=1)
        
        self.user_list = ttk.Treeview(self.users_frame, show="tree", selectmode="browse")
        self.user_list.grid(row=0, column=0, sticky="nsew")
        
        # Hide main interface initially
        self.chat_frame.grid_remove()
        self.channels_frame.grid_remove()
        self.users_frame.grid_remove()

    def connect(self):
        """Connect to IRC server"""
        server = self.server_var.get()
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
            
        nickname = self.nick_var.get()
        
        self.irc = IRCClient(server, port, nickname)
        if self.irc.connect():
            self.connected = True
            self.conn_frame.grid_remove()
            self.chat_frame.grid()
            self.channels_frame.grid()
            self.users_frame.grid()
            
            # Start message receiving thread
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.add_to_chat("System", f"Connected to {server}:{port} as {nickname}")
        else:
            messagebox.showerror("Error", "Failed to connect to server")

    def disconnect(self):
        """Disconnect from IRC server"""
        if self.irc and self.connected:
            self.connected = False
            self.irc.disconnect()
            self.show_connection_frame()
            self.add_to_chat("System", "Disconnected from server")

    def show_connection_frame(self):
        """Show the connection dialog"""
        self.chat_frame.grid_remove()
        self.channels_frame.grid_remove()
        self.users_frame.grid_remove()
        self.conn_frame.grid()

    def show_join_dialog(self):
        """Show dialog to join a channel"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        channel = simpledialog.askstring("Join Channel", "Enter channel name:")
        if channel:
            if not channel.startswith('#'):
                channel = f"#{channel}"
            self.irc.join_channel(channel)
            self.current_channel = channel

    def part_current_channel(self):
        """Leave the current channel"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        if self.irc.current_channel:
            self.irc.part_channel()
        else:
            messagebox.showinfo("Info", "Not in a channel")

    def send_message(self, event):
        """Send a message"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        message = self.message_input.get().strip()
        if message:
            if message.startswith('/'):
                # Handle commands
                self.handle_command(message[1:])
            else:
                # Send regular message
                if self.irc.current_channel:
                    self.irc.send_message(message)
                    # Add own message to chat
                    self.add_to_chat(self.irc.nickname, message)
                    self.message_input.delete(0, tk.END)
                else:
                    messagebox.showinfo("Info", "Not in a channel")

    def handle_command(self, command):
        """Handle IRC commands"""
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == 'join':
            if args:
                self.irc.join_channel(args[0])
            else:
                messagebox.showinfo("Info", "Usage: /join #channel")
        elif cmd == 'part':
            self.irc.part_channel()
        elif cmd == 'nick':
            if args:
                self.irc.change_nickname(args[0])
            else:
                messagebox.showinfo("Info", f"Current nickname: {self.irc.nickname}")
        elif cmd == 'msg':
            if len(args) >= 2:
                target = args[0]
                message = ' '.join(args[1:])
                self.irc.send_private_message(target, message)
            else:
                messagebox.showinfo("Info", "Usage: /msg <nickname> <message>")
        elif cmd == 'quit':
            self.disconnect()
        else:
            messagebox.showinfo("Info", f"Unknown command: {cmd}")
        
        self.message_input.delete(0, tk.END)

    def receive_messages(self):
        """Receive messages from IRC server"""
        while self.connected:
            try:
                data = self.irc.receive()
                if data:
                    messages = data.split('\r\n')
                    for message in messages:
                        if message:
                            self.message_queue.put(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.connected = False
                break

    def process_message_queue(self):
        """Process messages from the queue"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.irc.handle_message(message)
                self.update_gui_for_message(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_message_queue)

    def update_gui_for_message(self, message):
        """Update GUI based on received message"""
        msg = IRCMessage(message)
        
        if msg.command == "PRIVMSG":
            nick = msg.get_nickname()
            target = msg.params[0]
            content = msg.params[1]
            
            # Only display if it's not our own message (already displayed when sent)
            if nick != self.irc.nickname:
                self.add_to_chat(nick, content)
                
        elif msg.command == "JOIN":
            nick = msg.get_nickname()
            channel = msg.params[0]
            self.add_to_chat("System", f"{nick} has joined {channel}")
            self.update_channel_list()
            if nick == self.irc.nickname:
                self.current_channel = channel
                
        elif msg.command == "PART":
            nick = msg.get_nickname()
            channel = msg.params[0]
            self.add_to_chat("System", f"{nick} has left {channel}")
            self.update_channel_list()
            if nick == self.irc.nickname:
                self.current_channel = None
                
        elif msg.command == "NICK":
            old_nick = msg.get_nickname()
            new_nick = msg.params[0]
            self.add_to_chat("System", f"{old_nick} is now known as {new_nick}")
            
        elif msg.command.isdigit():
            code = int(msg.command)
            if code == 353:  # Names list
                channel = msg.params[2]
                users = msg.params[3].split()
                self.update_user_list(users)
                self.add_to_chat("System", f"Users in {channel}: {', '.join(users)}")

    def update_user_list(self, users):
        """Update the user list in the GUI"""
        self.user_list.delete(*self.user_list.get_children())
        for user in sorted(users):
            # Handle operator status (@) and voice status (+)
            if user.startswith(('@', '+')):
                status = user[0]
                username = user[1:]
            else:
                status = ''
                username = user
            self.user_list.insert("", "end", text=username, values=(status,))

    def update_channel_list(self):
        """Update the channel list"""
        if self.irc and self.irc.current_channel:
            self.channel_list.delete(*self.channel_list.get_children())
            self.channel_list.insert("", "end", text=self.irc.current_channel)
            self.current_channel = self.irc.current_channel

    def add_to_chat(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format system messages differently
        if sender == "System":
            formatted_message = f"[{timestamp}] * {message}\n"
        else:
            formatted_message = f"[{timestamp}] <{sender}> {message}\n"
            
        self.chat_display.insert(tk.END, formatted_message)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Store in message history
        if self.current_channel:
            if self.current_channel not in self.message_history:
                self.message_history[self.current_channel] = []
            self.message_history[self.current_channel].append({
                'timestamp': timestamp,
                'sender': sender,
                'message': message
            })

    def on_channel_select(self, event):
        """Handle channel selection"""
        selection = self.channel_list.selection()
        if selection:
            channel = self.channel_list.item(selection[0])['text']
            if channel != self.irc.current_channel:
                self.irc.join_channel(channel)

    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = IRCGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 