#!/usr/bin/env python3
import socket
import sys
import logging
import re
import threading
import queue
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IRCMessage:
    def __init__(self, raw_message):
        self.raw = raw_message.strip()
        self.prefix = ''
        self.command = ''
        self.params = []
        self.timestamp = datetime.now()
        self.parse_message()

    def parse_message(self):
        if not self.raw:
            return

        parts = self.raw.split(' ')
        idx = 0

        # Parse prefix if exists
        if parts[0].startswith(':'):
            self.prefix = parts[0][1:]
            idx += 1

        # Parse command
        if idx < len(parts):
            self.command = parts[idx].upper()
            idx += 1

        # Parse parameters
        while idx < len(parts):
            if parts[idx].startswith(':'):
                # This is the last parameter, can contain spaces
                self.params.append(' '.join(parts[idx:]).lstrip(':'))
                break
            else:
                self.params.append(parts[idx])
            idx += 1

    def get_nickname(self):
        """Extract nickname from prefix."""
        if '!' in self.prefix:
            return self.prefix.split('!')[0]
        return self.prefix

class IRCClient:
    def __init__(self, server, port, nickname="IRCPyClient", username="ircpy", realname="IRC Python Client"):
        """Initialize IRC client with server and port."""
        self.server = server
        self.port = port
        self.socket = None
        self.nickname = nickname
        self.username = username
        self.realname = realname
        self.registered = False
        self.current_channel = None
        self.input_queue = queue.Queue()
        self.running = False
        self.nick_attempts = 0
        self.max_nick_attempts = 5
        self.message_history = defaultdict(list)
        self.max_history = 100
        
    def connect(self):
        """Establish connection to the IRC server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info(f"Connecting to {self.server}:{self.port}")
            self.socket.connect((self.server, self.port))
            logger.info("Successfully connected to IRC server")
            
            # Send initial registration
            self.register()
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False

    def register(self):
        """Send initial NICK and USER registration messages."""
        self.nick_attempts = 0
        self.send_raw(f"NICK {self.nickname}")
        self.send_raw(f"USER {self.username} 0 * :{self.realname}")
            
    def disconnect(self):
        """Close the connection to the IRC server."""
        if self.socket:
            try:
                # Leave all channels first
                if self.current_channel:
                    self.part_channel(self.current_channel)
                
                # Send quit message and wait briefly for server response
                quit_msg = "QUIT :Goodbye!"
                self.send_raw(quit_msg)
                
                # Give the server a moment to process our quit message
                self.socket.settimeout(2.0)
                try:
                    # Try to receive any final messages
                    while True:
                        data = self.receive()
                        if not data:
                            break
                        messages = data.split('\r\n')
                        for message in messages:
                            if message:
                                self.handle_message(message)
                except socket.timeout:
                    pass  # Expected timeout after server closes connection
                
                # Close the socket
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    pass  # Socket might already be shut down
                self.socket.close()
                self.socket = None
                logger.info("Gracefully disconnected from IRC server")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
            finally:
                self.current_channel = None
                self.registered = False
            
    def send_raw(self, message):
        """Send a raw message to the IRC server."""
        if not self.socket:
            logger.error("Not connected to server")
            return False
            
        try:
            # IRC messages are terminated with \r\n
            full_message = f"{message}\r\n"
            self.socket.send(full_message.encode('utf-8'))
            logger.info(f"Sent: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False

    def store_message(self, target, message, from_nick=None):
        """Store message in history."""
        timestamp = datetime.now()
        entry = {
            'timestamp': timestamp,
            'from': from_nick or self.nickname,
            'message': message
        }
        self.message_history[target].append(entry)
        
        # Trim history if needed
        if len(self.message_history[target]) > self.max_history:
            self.message_history[target] = self.message_history[target][-self.max_history:]
            
    def receive(self):
        """Receive data from the IRC server."""
        if not self.socket:
            logger.error("Not connected to server")
            return None
            
        try:
            # IRC messages are typically limited to 512 bytes
            data = self.socket.recv(512).decode('utf-8')
            if data:
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to receive data: {str(e)}")
            return None

    def join_channel(self, channel):
        """Join an IRC channel."""
        if not channel.startswith('#'):
            channel = f"#{channel}"
        self.send_raw(f"JOIN {channel}")

    def part_channel(self, channel=None):
        """Leave the current or specified channel."""
        if channel is None:
            channel = self.current_channel
        if channel:
            self.send_raw(f"PART {channel}")
            if channel == self.current_channel:
                self.current_channel = None

    def send_message(self, message, target=None):
        """Send a message to the current channel or specified target."""
        if not target:
            target = self.current_channel
        if not target:
            logger.error("No target specified and not in a channel")
            return False
            
        # Store message in history
        self.store_message(target, message)
        return self.send_raw(f"PRIVMSG {target} :{message}")

    def send_private_message(self, target, message):
        """Send a private message to a user."""
        if not target or not message:
            return False
        return self.send_message(message, target)

    def format_message(self, timestamp, from_nick, message, is_private=False):
        """Format a chat message for display."""
        time_str = timestamp.strftime("%H:%M:%S")
        if is_private:
            return f"[{time_str}] *{from_nick}*: {message}"
        return f"[{time_str}] {from_nick}: {message}"

    def show_history(self, target=None, count=10):
        """Show message history for the current or specified target."""
        if not target:
            target = self.current_channel
        if not target:
            print("No target specified and not in a channel")
            return
            
        messages = self.message_history.get(target, [])
        if not messages:
            print(f"No message history for {target}")
            return
            
        print(f"\nLast {min(count, len(messages))} messages for {target}:")
        for msg in messages[-count:]:
            is_private = not target.startswith('#')
            print(self.format_message(
                msg['timestamp'],
                msg['from'],
                msg['message'],
                is_private
            ))

    def handle_user_input(self):
        """Handle user input in a separate thread."""
        print("Enter commands or messages. Type /help for available commands.")
        while self.running:
            try:
                user_input = input()
                if user_input.startswith('/'):
                    self.handle_command(user_input[1:])
                elif self.current_channel:
                    self.send_message(user_input)
                else:
                    print("Not in a channel. Join a channel first with /join #channel")
            except EOFError:
                break

    def handle_command(self, command):
        """Handle IRC commands entered by the user."""
        parts = command.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == 'join':
            if args:
                self.join_channel(args[0])
            else:
                print("Usage: /join #channel")
        elif cmd == 'part':
            self.part_channel()
        elif cmd == 'nick':
            if args:
                self.change_nickname(args[0])
            else:
                print(f"Current nickname: {self.nickname}")
                print("Usage: /nick new_nickname")
        elif cmd == 'msg':
            if len(args) >= 2:
                target = args[0]
                message = ' '.join(args[1:])
                self.send_private_message(target, message)
            else:
                print("Usage: /msg <nickname> <message>")
        elif cmd == 'history':
            count = 10
            target = None
            if args:
                if args[0].isdigit():
                    count = int(args[0])
                else:
                    target = args[0]
                if len(args) > 1 and args[1].isdigit():
                    count = int(args[1])
            self.show_history(target, count)
        elif cmd == 'quit':
            self.running = False
            self.disconnect()
        elif cmd == 'help':
            print("Available commands:")
            print("  /join #channel - Join a channel")
            print("  /part - Leave current channel")
            print("  /nick [new_nickname] - View or change nickname")
            print("  /msg <nickname> <message> - Send private message")
            print("  /history [target] [count] - Show message history")
            print("  /quit - Quit the client")
            print("  /help - Show this help message")
        else:
            print(f"Unknown command: {cmd}")

    def handle_message(self, message):
        """Handle incoming IRC messages."""
        irc_msg = IRCMessage(message)
        
        # Log the parsed message for debugging
        logger.debug(f"Prefix: {irc_msg.prefix}, Command: {irc_msg.command}, Params: {irc_msg.params}")
        
        # Handle PING messages
        if irc_msg.command == "PING":
            self.send_raw(f"PONG {irc_msg.params[0]}")
            return
            
        # Handle numeric responses
        if irc_msg.command.isdigit():
            code = int(irc_msg.command)
            if code == 1:
                logger.info("Successfully registered with the server!")
                self.registered = True
            elif code == 432:  # Erroneous nickname
                print("Error: Invalid nickname format")
                if not self.registered:
                    self.nickname = f"Guest{hash(self.nickname) % 1000:03d}"
                    self.send_raw(f"NICK {self.nickname}")
            elif code == 433:  # Nickname already in use
                self.nick_attempts += 1
                if self.nick_attempts < self.max_nick_attempts:
                    new_nick = f"{self.nickname}{self.nick_attempts}"
                    print(f"Nickname {self.nickname} already in use, trying {new_nick}")
                    self.nickname = new_nick
                    self.send_raw(f"NICK {self.nickname}")
                else:
                    print("Failed to find an available nickname")
                    if not self.registered:
                        self.running = False
            elif code == 353:  # Channel names list
                channel = irc_msg.params[2]
                users = irc_msg.params[3].split()
                print(f"Users in {channel}: {', '.join(users)}")
            elif code == 465:  # You're banned
                print("Error: You are banned from this server")
                self.running = False
            elif code == 471:  # Channel is full
                print(f"Error: Channel {irc_msg.params[1]} is full")
            elif code == 473:  # Channel is invite only
                print(f"Error: Channel {irc_msg.params[1]} is invite only")
            elif code == 474:  # Banned from channel
                print(f"Error: You are banned from channel {irc_msg.params[1]}")
            elif code == 475:  # Channel requires key
                print(f"Error: Channel {irc_msg.params[1]} requires a key")
        
        # Handle QUIT messages
        elif irc_msg.command == "QUIT":
            nick = irc_msg.get_nickname()
            quit_msg = irc_msg.params[0] if irc_msg.params else "No message"
            if nick == self.nickname:
                print(f"You have quit: {quit_msg}")
            else:
                print(f"{nick} has quit: {quit_msg}")
        
        # Handle ERROR messages
        elif irc_msg.command == "ERROR":
            error_msg = irc_msg.params[0] if irc_msg.params else "Unknown error"
            print(f"Server error: {error_msg}")
            self.running = False
        
        # Handle other messages (NICK, JOIN, PART, PRIVMSG)
        elif irc_msg.command == "NICK":
            old_nick = irc_msg.get_nickname()
            new_nick = irc_msg.params[0]
            if old_nick == self.nickname:
                self.nickname = new_nick
                print(f"You are now known as {new_nick}")
            else:
                print(f"{old_nick} is now known as {new_nick}")
        
        elif irc_msg.command == "JOIN":
            channel = irc_msg.params[0]
            nick = irc_msg.get_nickname()
            if nick == self.nickname:
                self.current_channel = channel
                print(f"Joined channel: {channel}")
            else:
                print(f"{nick} has joined {channel}")
        
        elif irc_msg.command == "PART":
            channel = irc_msg.params[0]
            nick = irc_msg.get_nickname()
            if nick == self.nickname:
                if channel == self.current_channel:
                    self.current_channel = None
                print(f"Left channel: {channel}")
            else:
                print(f"{nick} has left {channel}")
        
        elif irc_msg.command == "PRIVMSG":
            nick = irc_msg.get_nickname()
            target = irc_msg.params[0]
            message = irc_msg.params[1]
            
            # Store message in history
            if target.startswith('#'):
                self.store_message(target, message, nick)
            else:
                # For private messages, store in both sender and receiver history
                self.store_message(nick, message, nick)
                if target == self.nickname:
                    print(self.format_message(datetime.now(), nick, message, True))
                
            if target == self.nickname:
                print(f"Private message from {nick}: {message}")
            else:
                print(f"{nick}: {message}")
        
        # Print other server messages
        elif irc_msg.params:
            print(f"{irc_msg.prefix}: {irc_msg.params[-1]}")

def main():
    # Example usage
    client = IRCClient('irc.libera.chat', 6667)
    exit_code = 0
    
    if client.connect():
        client.running = True
        
        # Start input handling thread
        input_thread = threading.Thread(target=client.handle_user_input)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            # Message handling loop
            while client.running:
                try:
                    data = client.receive()
                    if data:
                        # Handle each complete message
                        messages = data.split('\r\n')
                        for message in messages:
                            if message:  # Skip empty messages
                                client.handle_message(message)
                    else:  # Server closed connection
                        print("Lost connection to server")
                        client.running = False
                        exit_code = 1
                except socket.error as e:
                    print(f"Connection error: {str(e)}")
                    client.running = False
                    exit_code = 1
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        finally:
            client.running = False
            client.disconnect()
            sys.exit(exit_code)

if __name__ == "__main__":
    main() 