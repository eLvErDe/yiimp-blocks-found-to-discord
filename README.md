# What it does

Poll a [Yiimp pool] block found result page (usually on /site/found\_results) and post a message to [Discord] chat room.
It also feature a currency conversion to add blocks value in BTC and USDT (USD parity) using [stock.exchange] and [Cryptopia] markets API.

Single file app all written in Python 3 asyncio, it should be very easy to modify to use additionnal markets API and or different endpoints.


# System service installation

1. Install depencencies (Python 3.5+)
```
sudo apt install python3-aiohttp python3-bs4
```

2. Install script
```
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/yiimp-blocks-found-to-discord.py -O /usr/local/bin/yiimp-blocks-found-to-discord.py
sudo chmod 0755 /usr/local/bin/yiimp-blocks-found-to-discord.py
```

3. Register as a systemd service
```
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/systemd/service -O /etc/systemd/system/yiimp-blocks-found-to-discord.service 
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/systemd/default -O /etc/default/yiimp-blocks-found-to-discord
sudo systemctl daemon-reload
```

4. Edit `/etc/default/yiimp-blocks-found-to-discord` to set the correct pool URL and Discord web hook URL

5. Mark as autostart and start it
```
sudo systemctl enable yiimp-blocks-found-to-discord
sudo systemctl start yiimp-blocks-found-to-discord
```

6. Check application logs
```
sudo tail -n 50 -f /var/log/syslog | grep yiimp-blocks-found-to-discord
```

[Yiimp pool]: https://github.com/tpruvot/yiimp
[Discord]: https://discordapp.com/
[stock.exchange]: https://stocks.exchange/
[Cryptopia]: https://www.cryptopia.co.nz/
