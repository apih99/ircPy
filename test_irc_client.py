#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, patch
import socket
from datetime import datetime
from irc_client import IRCClient, IRCMessage

class TestIRCMessage(unittest.TestCase):
    def test_parse_simple_message(self):
        """Test parsing a simple IRC message without prefix"""
        msg = IRCMessage("PING :server1")
        self.assertEqual(msg.command, "PING")
        self.assertEqual(msg.params, ["server1"])
        self.assertEqual(msg.prefix, "")

    def test_parse_prefixed_message(self):
        """Test parsing a message with prefix"""
        msg = IRCMessage(":nick!user@host PRIVMSG #channel :Hello World!")
        self.assertEqual(msg.prefix, "nick!user@host")
        self.assertEqual(msg.command, "PRIVMSG")
        self.assertEqual(msg.params, ["#channel", "Hello World!"])

    def test_get_nickname(self):
        """Test extracting nickname from prefix"""
        msg = IRCMessage(":nick!user@host PRIVMSG #channel :Hello")
        self.assertEqual(msg.get_nickname(), "nick")

class TestIRCClient(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.client = IRCClient("test.server", 6667)
        self.client.socket = Mock()

    def test_connect_success(self):
        """Test successful connection"""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value = Mock()
            client = IRCClient("test.server", 6667)
            self.assertTrue(client.connect())
            mock_socket.return_value.connect.assert_called_once_with(("test.server", 6667))

    def test_connect_failure(self):
        """Test connection failure"""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = socket.error()
            client = IRCClient("test.server", 6667)
            self.assertFalse(client.connect())

    def test_registration(self):
        """Test initial registration sequence"""
        self.client.send_raw = Mock()
        self.client.register()
        self.client.send_raw.assert_any_call("NICK IRCPyClient")
        self.client.send_raw.assert_any_call("USER ircpy 0 * :IRC Python Client")

    def test_join_channel(self):
        """Test joining a channel"""
        self.client.send_raw = Mock()
        self.client.join_channel("#test")
        self.client.send_raw.assert_called_once_with("JOIN #test")

        # Test auto-prepending #
        self.client.join_channel("test2")
        self.client.send_raw.assert_called_with("JOIN #test2")

    def test_part_channel(self):
        """Test leaving a channel"""
        self.client.send_raw = Mock()
        self.client.current_channel = "#test"
        self.client.part_channel()
        self.client.send_raw.assert_called_once_with("PART #test")
        self.assertIsNone(self.client.current_channel)

    def test_send_message(self):
        """Test sending messages"""
        self.client.send_raw = Mock()
        self.client.current_channel = "#test"
        
        # Test channel message
        self.client.send_message("Hello World!")
        self.client.send_raw.assert_called_with("PRIVMSG #test :Hello World!")
        
        # Test private message
        self.client.send_message("Hello User!", "user1")
        self.client.send_raw.assert_called_with("PRIVMSG user1 :Hello User!")

    def test_message_history(self):
        """Test message history functionality"""
        channel = "#test"
        self.client.store_message(channel, "Message 1", "user1")
        self.client.store_message(channel, "Message 2", "user2")
        
        history = self.client.message_history[channel]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['message'], "Message 1")
        self.assertEqual(history[0]['from'], "user1")
        self.assertEqual(history[1]['message'], "Message 2")
        self.assertEqual(history[1]['from'], "user2")

    def test_handle_ping(self):
        """Test PING/PONG handling"""
        self.client.send_raw = Mock()
        self.client.handle_message("PING :server1.test.net")
        self.client.send_raw.assert_called_once_with("PONG server1.test.net")

    def test_handle_nick_change(self):
        """Test nickname change handling"""
        self.client.send_raw = Mock()
        
        # Test own nickname change
        self.client.nickname = "OldNick"
        self.client.handle_message(":OldNick!user@host NICK :NewNick")
        self.assertEqual(self.client.nickname, "NewNick")
        
        # Test other user's nickname change
        self.client.handle_message(":User1!user@host NICK :User2")
        self.assertEqual(self.client.nickname, "NewNick")  # Own nick unchanged

    def test_handle_join_part(self):
        """Test JOIN/PART message handling"""
        self.client.nickname = "TestUser"
        
        # Test own join
        self.client.handle_message(":TestUser!user@host JOIN :#channel")
        self.assertEqual(self.client.current_channel, "#channel")
        
        # Test own part
        self.client.handle_message(":TestUser!user@host PART :#channel")
        self.assertIsNone(self.client.current_channel)

    def test_handle_privmsg(self):
        """Test private message handling"""
        self.client.store_message = Mock()
        self.client.nickname = "TestUser"
        
        # Test channel message
        self.client.handle_message(":User1!user@host PRIVMSG #channel :Hello all!")
        self.client.store_message.assert_called_with("#channel", "Hello all!", "User1")
        
        # Test private message
        self.client.handle_message(":User1!user@host PRIVMSG TestUser :Hello!")
        self.client.store_message.assert_called_with("User1", "Hello!", "User1")

    def test_message_formatting(self):
        """Test message formatting"""
        timestamp = datetime.now()
        
        # Test channel message format
        formatted = self.client.format_message(timestamp, "User1", "Hello!", False)
        self.assertIn("User1: Hello!", formatted)
        
        # Test private message format
        formatted = self.client.format_message(timestamp, "User1", "Hello!", True)
        self.assertIn("*User1*: Hello!", formatted)

def main():
    unittest.main()

if __name__ == '__main__':
    main() 