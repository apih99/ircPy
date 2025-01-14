# Python IRC Client

A modern IRC (Internet Relay Chat) client implementation in Python with both GUI and command-line interfaces. This client follows the IRC protocol specification (RFC 2812) and provides a user-friendly interface for IRC communication.

## Features

### Core Functionality
- Full IRC protocol support (RFC 2812)
- Server connection management
- Channel operations (join/part)
- Private messaging
- Nickname management
- Message history tracking
- PING/PONG server keepalive

### GUI Features
- Modern dark theme interface
- Three-panel layout:
  - Channel list (left)
  - Chat area (center)
  - User list (right)
- Message formatting with timestamps
- User status indicators (@ for operators, + for voice)
- Command input support
- Real-time updates

### Command Support
- `/join #channel` - Join a channel
- `/part` - Leave current channel
- `/nick nickname` - Change nickname
- `/msg user message` - Send private message
- `/quit` - Disconnect and exit
- `/help` - Show available commands

## Installation

1. Clone the repository:
```bash
git clone https://github.com/apih99/ircPy.git
cd ircPy
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Client
Run the GUI version:
```bash
python irc_gui.py
```

### Command-Line Client
Run the command-line version:
```bash
python irc_client.py
```

## Project Structure

```
ircPy/
├── irc_client.py     # Core IRC client implementation
├── irc_gui.py        # GUI implementation
├── requirements.txt  # Project dependencies
├── README.md        # Documentation
└── test_irc_client.py # Unit tests
```

## Implementation Details

### IRC Client (irc_client.py)
- Implements core IRC protocol functionality
- Handles server communication
- Message parsing and formatting
- Channel and user management
- Event handling

### GUI Client (irc_gui.py)
- Built with tkinter
- Real-time message display
- User interface components:
  - Connection dialog
  - Channel management
  - Message input
  - User list
- Event-driven architecture

### Testing (test_irc_client.py)
- Unit tests for core functionality
- Message parsing tests
- Connection handling tests
- Command processing tests

## IRC Protocol Support

### Implemented RFC 2812 Features
- Connection registration
- Channel operations
- Private messages
- Server queries
- Error handling

### Message Types
- PRIVMSG - Private and channel messages
- JOIN - Channel joining
- PART - Channel leaving
- NICK - Nickname changes
- PING/PONG - Server keepalive
- Numeric responses (001-999)

## Development

### Requirements
- Python 3.6+
- tkinter (for GUI)
- socket (for network communication)

### Running Tests
```bash
python -m unittest test_irc_client.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Error Handling

The client handles various error scenarios:
- Connection failures
- Nickname collisions
- Channel access restrictions
- Server disconnections
- Invalid commands
- Message parsing errors

## Configuration

Default settings:
- Server: irc.libera.chat
- Port: 6667
- Default nickname: IRCPyUser

## Known Limitations

- Single channel view at a time
- Basic authentication only
- No SSL/TLS support
- Limited formatting options

## Future Improvements

Planned features:
- Multi-channel view
- SSL/TLS support
- Rich text formatting
- File transfer support
- Channel operator tools
- Custom themes
- Message logging
- Auto-reconnect
- Server bookmarks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on RFC 2812 IRC Protocol specification
- Inspired by classic IRC clients
- Built as part of the Coding Challenges project


## Version History

- 1.0.0 - Initial release
  - Basic IRC functionality
  - GUI implementation
  - Command support
  - Message history 